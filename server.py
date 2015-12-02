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
tagger = None
idf_doc_count = None
idf_table = None


@app.route('/')
def index():
    return "OK\n"


@app.route('/', methods=['POST'])
def post_request():
    file = request.files['file']
    post_id = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+\
            str(random.randint(10000, 99999))
    post_dir = os.path.join(app.config['UPLOAD_FOLDER'], post_id)
    os.mkdir(post_dir)

    file_name = secure_filename(file.filename)
    file_path = os.path.join(post_dir, file_name)
    file.save(os.path.join(file_path))

    data, code = process_file(file_path)
    json_response = json.dumps(data).encode('utf-8')

    response = flask.Response(json_response,
                              content_type='application/json; charset=utf-8')
    response.headers.add('content-length', len(json_response))
    response.status_code = code
    return response


def process_file(file_path):
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
        return {"Eror": "Unsupported file type: {}".format(file_info)}, 200

    if not lines:
        return {"Error": "Empty file"}, 200
    return keywords.get_keywords(lines, tagger, idf_doc_count, idf_table), 200


def lines_from_txt_file(file_path, encoding='utf-8'):
    if type(file_path) is str:
        f = codecs.open(file_path, 'r', encoding)
    else:
        f = file_path
    content = [l.strip() for l in f]
    f.close()
    return content


def lines_from_alto_file(file_path):
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
    parser.add_argument("--cs-morphodita", help="Path to Czech model for morphodita.")
    parser.add_argument("--cs-idf", help="Czech idf model.")
    args = parser.parse_args()

    tagger = keywords.Morphodita(args.cs_morphodita)

    f_idf = open(args.cs_idf, 'rb')
    idf_doc_count = float(pickle.load(f_idf))
    idf_table = pickle.load(f_idf)
    f_idf.close()

    app.run(debug=True)
