#!/usr/bin/env python

import flask
from flask import Flask
from flask import request
from werkzeug import secure_filename
import os, random, datetime, codecs
import sys, json, magic
import cPickle as pickle
import regex as re
import keywords
import argparse
import xml.etree.ElementTree
import zipfile

app = Flask(__name__)
upload_dir = "uploads"
cs_tagger = None
cs_idf_doc_count = None
cs_idf_table = None

en_tagger = None
en_idf_doc_count = None
en_idf_table = None

@app.route('/')
def index():
    return "{}\n"

def root_dir():  # pragma: no cover
        return os.path.abspath(os.path.dirname(__file__))

def get_file(file_name):
    try:
        src = os.path.join(root_dir(), file_name)
        return open(src).read()
    except IOError as exc:
        return str(exc)

@app.route('/web', methods=['GET'])
def show_web():
    content = get_file("web.html")
    print content
    return flask.Response(content, mimetype="text/html")

@app.route('/demo', methods=['GET'])
def show_simple_demo():
    content = get_file("web.html")
    content = re.sub(r"\$\(\'#header", "//", content)
    content = re.sub(r"\$\(\'#footer", "//", content)
    return flask.Response(content, mimetype="text/html")


@app.route('/', methods=['POST'])
def post_request():
    start_time = datetime.datetime.now()
    if 'file' in request.files:
        file = request.files['file']
    else:
        class _file_wrapper(object):
            def __init__(self, data):
                self._data = data
                import uuid
                self.filename = str(uuid.uuid4())
            def save(self, path):
                with codecs.open(path, mode="w+", encoding="utf-8") as fout:
                    fout.write(self._data)
        file = _file_wrapper(request.form["data"])

    tagger = cs_tagger
    idf_doc_count = cs_idf_doc_count
    idf_table = cs_idf_table

    json_response = None

    try:
        post_id = datetime.datetime.now().strftime("%Y-%m-%d/%H/%M-%S-")+\
                str(random.randint(10000, 99999))
        post_dir = os.path.join(upload_dir, post_id)
        os.makedirs(post_dir)

        if request.args.get('language') == 'en':
            tagger = en_tagger
            idf_doc_count = en_idf_doc_count
            idf_table = en_idf_table
        elif request.args.get('language') == 'cs':
            pass
        elif request.args.get('language'):
            raise Exception('Unsupported language {}'.format(request.args.get('language')))

        if request.args.get('threshold'):
            try:
                threshold = float(request.args.get('threshold'))
            except:
                raise Exception("Threshold \"{}\" is not valid float.".format(request.args.get("threshold")))
        else:
            threshold = 0.2

        if request.args.get("maximum-words"):
            try:
                maximum_words = int(request.args.get('maximum-words'))
            except:
                raise Exception("Maximum number of words \"{}\" is not an integer.".format(request.args.get("maximum-words")))
        else:
            maximum_words = 15


        file_name = secure_filename(file.filename)
        file_path = os.path.join(post_dir, file_name)
        file.save(os.path.join(file_path))

        data, code = \
                process_file(file_path, tagger, idf_doc_count, idf_table, threshold, maximum_words)
    except Exception as e:
        code = 400
        data = {"error": e.message}
    finally:
        json_response = json.dumps(data)
        print json_response.encode('unicode-escape')

        log = {}
        log['remote_addr'] = request.remote_addr
        log['response_json'] = data
        log['response_code'] = code
        log['time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
        log['duration'] = (datetime.datetime.now() - start_time).total_seconds()
        f_log = open(os.path.join(post_dir, "log.json"), 'w')
        json.dump(log, f_log)
        f_log.close()

        response = flask.Response(json_response,
                                  content_type='application/json; charset=utf-8')
        response.headers.add('content-length', len(json_response.encode('utf-8')))
        response.status_code = code
        return response


def process_file(file_path, tagger, idf_doc_count, idf_table, threshold, maximum_words):
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
    elif re.match("^ASCII text", file_info):
        lines = lines_from_txt_file(file_path, encoding='utf-8')
    elif re.match('^XML 1.0 document', file_info) and \
            (file_path.endswith('.alto') or file_path.endswith('.xml')):
        lines = lines_from_alto_file(file_path)
    elif re.match('^Zip archive data', file_info):
        lines = lines_from_zip_file(file_path)
    else:
        return {"eror": "Unsupported file type: {}".format(file_info)}, 400

    if not lines:
        return {"error": "Empty file"}, 400
    return keywords.get_keywords(lines, tagger, idf_doc_count, idf_table, threshold, maximum_words), 200


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
        raise Exception("XML is not ALTO file (does not contain layout object).")
    for page in layout.getchildren():
        if not page.tag.endswith("Page"):
            continue

        text_lines = layout.findall(".//{http://www.loc.gov/standards/alto/ns-v2#}TextLine")

        for text_line in text_lines:
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
    alto_files = [n for n in archive.namelist() if n.endswith(".alto") or n.endswith(".xml")]
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
    parser.add_argument("--port", help="Port the server runs on", type=int, default=5000)
    parser.add_argument("--host", help="IP address the server will run at", type=str, default="127.0.0.1")
    args = parser.parse_args()

    if os.path.exists(args.cs_morphodita):
        cs_tagger = keywords.Morphodita(args.cs_morphodita)
    else:
        print >> sys.stderr, "File with Czech Morphodita model does not exist: {}".format(args.cs_morphodita)
        exit(1)

    if os.path.exists(args.cs_idf):
        f_idf = open(args.cs_idf, 'rb')
        cs_idf_doc_count = float(pickle.load(f_idf))
        cs_idf_table = pickle.load(f_idf)
        f_idf.close()
    else:
        print >> sys.stderr, "File with Czech IDF model does not exist: {}".format(args.cs_idf)
        exit(1)

    if os.path.exists(args.en_morphodita):
        en_tagger = keywords.Morphodita(args.en_morphodita)
    else:
        print >> sys.stderr, "File with English Morphodita model does not exist: {}".format(args.en_morphodita)
        exit(1)

    if os.path.exists(args.en_idf):
        f_idf = open(args.en_idf, 'rb')
        en_idf_doc_count = float(pickle.load(f_idf))
        en_idf_table = pickle.load(f_idf)
        f_idf.close()
    else:
        print >> sys.stderr, "File with English IDF model does not exist: {}".format(args.en_idf)
        exit(1)

    app.run(debug=True, host=args.host, port=args.port)
