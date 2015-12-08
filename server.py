#!/usr/bin/env python

import flask
from flask import Flask
from flask import request
from werkzeug import secure_filename
import os, random, datetime, codecs
import json, magic
import cPickle as pickle
import regex as re
import keywords
import argparse
import xml.etree.ElementTree
import zipfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
cs_tagger = None
cs_idf_doc_count = None
cs_idf_table = None

en_tagger = None
en_idf_doc_count = None
en_idf_table = None

@app.route('/')
def index():
    return "OK\n"


@app.route('/', methods=['POST'])
def post_request():
    file = request.files['file']

    tagger = cs_tagger
    idf_doc_count = cs_idf_doc_count
    idf_table = cs_idf_table

    json_response = None

    try:
        if request.args.get('language') == 'en':
            tagger = en_tagger
            idf_doc_count = en_idf_doc_count
            idf_table = en_idf_table
        elif request.args.get('language') == 'cs':
            pass
        elif request.args.get('language'):
            raise Exception('Unsupported language {}'.format(request.args.get('language')))

        post_id = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+\
                str(random.randint(10000, 99999))
        post_dir = os.path.join(app.config['UPLOAD_FOLDER'], post_id)
        os.mkdir(post_dir)

        file_name = secure_filename(file.filename)
        file_path = os.path.join(post_dir, file_name)
        file.save(os.path.join(file_path))

        data, code = process_file(file_path, tagger, idf_doc_count, idf_table)
        json_response = json.dumps(data).decode('unicode-escape')
    except Exception as e:
        code = 400
        json_response = json.dumps({"error": e.message})
    finally:
        print json_response
        response = flask.Response(json_response,
                                  content_type='application/json; charset=utf-8')
        response.headers.add('content-length', len(json_response))
        response.status_code = code
        return response


def process_file(file_path, tagger, idf_doc_count, idf_table):
    """
    Takes the uploaded file, detecs its type (plain text, alto XML, zip)
    and calls a parsing function accordingly. If everything succeeds it
    returns keywords and 200 code, returns an error otherwise.
    """
    file_info = magic.from_file(file_path)
    lines = []
    if re.match("^UTF-8 Unicode (with BOM) text", file_info):
        lines = lines_from_txt_file(file_path, encoding='utf-8-sig')
    elif re.match("^UTF-8 Unicode", file_info):
        lines = lines_from_txt_file(file_path, encoding='utf-8')
    elif re.match('^XML 1.0 document', file_info) and file_path.endswith('.alto'):
        lines = lines_from_alto_file(file_path)
    elif re.match('^Zip archive data', file_info):
        lines = lines_from_zip_file(file_path)
    else:
        return {"eror": "Unsupported file type: {}".format(file_info)}, 400

    if not lines:
        return {"error": "Empty file"}, 400
    return keywords.get_keywords(lines, tagger, idf_doc_count, idf_table), 200


def lines_from_txt_file(file_path, encoding='utf-8'):
    """
    Loads lines of text from a plain text file.

    :param file_path: Path to the alto file or a file-like object.

    """
    if type(file_path) is str:
        f = codecs.open(file_path, 'r', encoding)
    else:
        f = file_path
    content = [l.strip() for l in f]
    f.close()
    return content


def lines_from_alto_file(file_path):
    """
    Loads lines of text from a provided alto file.

    :param file_path: Path to the alto file or a file-like object.

    """
    e = xml.etree.ElementTree.parse(file_path).getroot()
    layout = None
    for c in e.getchildren():
        if c.tag.endswith('Layout'):
            layout = c
            break
    if layout is None:
        raise Exception("Alto XML does not contain layout object.")
    for page in layout.getchildren():
        if not page.tag.endswith("Page"):
            continue
        for print_space in page.getchildren():
            if not print_space.tag.endswith("PrintSpace"):
                continue
            for text_block in print_space.getchildren():
                if not text_block.tag.endswith('TextBlock'):
                    continue
                for text_line in text_block.getchildren():
                    if not text_line.tag.endswith('TextLine'):
                        continue
                    line_words = []
                    for string in text_line.getchildren():
                        if not string.tag.endswith('String'):
                            continue
                        line_words.append(string.attrib['CONTENT'])
                    yield " ".join(line_words)

def lines_from_zip_file(file_path):
    """
    Loads lines of text from a provided zip file. If it contains alto file, it
    uses them, otherwise looks for txt files. Files can in an arbitrary depth.

    :param file_path: Path to the uploaded zip file.
    :type file_path: str

    """
    archive = zipfile.ZipFile(file_path)
    alto_files = [n for n in archive.namelist() if n.endswith(".alto")]
    if alto_files:
        for f_name in alto_files:
            for line in lines_from_alto_file(archive.open(f_name)):
                yield line
    else:
        txt_files = [n for n in archive.namelist() if n.endswith(".txt")]
        if not txt_files:
            raise Exception("Archive contains neither alto files nor text files.")
        for f_name in txt_files:
            for line in lines_from_txt_file(archive.open(f_name)):
                yield line

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runs the KER server.')
    parser.add_argument("--cs-morphodita", help="Path to a Czech tagger model for Morphodita.", required=True)
    parser.add_argument("--cs-idf", help="Czech idf model.", required=True)
    parser.add_argument("--en-morphodita", help="Path to a English tagger model for Morphodita.", required=True)
    parser.add_argument("--en-idf", help="English idf model.", required=True)
    args = parser.parse_args()

    cs_tagger = keywords.Morphodita(args.cs_morphodita)

    f_idf = open(args.cs_idf, 'rb')
    cs_idf_doc_count = float(pickle.load(f_idf))
    cs_idf_table = pickle.load(f_idf)
    f_idf.close()

    en_tagger = keywords.Morphodita(args.en_morphodita)

    f_idf = open(args.en_idf, 'rb')
    en_idf_doc_count = float(pickle.load(f_idf))
    en_idf_table = pickle.load(f_idf)
    f_idf.close()

    app.run(debug=True)