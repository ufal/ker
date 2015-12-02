#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import regex as re
import sys, os, math
import cPickle as pickle

stopwords = set((u"odstavec kapitola obsah část cvičení metoda druh rovnice"+
    u"rejstřík literatura seznam základ příklad stanovení definice výpočet"+
    u"csc prof ing doc"+
    u"postup úvod poznámka závěr úloha zadání procvičení").split(" "))

def clean_lines(lines):
    """
    Returns the text that are present in a file after removing formating
    marks
    """
    for line in lines:
        orginal = line.strip()
        line = line.strip()
        line = re.sub("[[:space:]]+\([^(]*\)", "", line).strip()
        line = re.sub(r"[0-9]+(\.[0-9]+)*\.?[[:space:]]*", "", line).strip()
        line = re.sub(r"[[:space:]]*((\.+)|([[:space:]]+))[[:space:]]*[0-9]*$", "", line).strip()
        if line:
            yield line

class Morphodita(object):
    def __init__(self, model_file):
        from ufal.morphodita import Tagger, Forms, TaggedLemmas, TokenRanges
        self.tagger = Tagger.load(model_file)
        self.forms = Forms()
        self.lemmas = TaggedLemmas()
        self.tokens = TokenRanges()
        self.tokenizer = self.tagger.newTokenizer()

    def normalize(self, text):
        self.tokenizer.setText(text)
        lemmas = []
        while self.tokenizer.nextSentence(self.forms, self.tokens):
            self.tagger.tag(self.forms, self.lemmas)
            lemmas += [l.lemma.lower() for l in self.lemmas \
                    if (l.tag == 'NN' or l.tag == 'AA') and len(l.lemma) > 2 and l.lemma not in stopwords]
        return lemmas


def get_keywords(lines, tagger, idf_doc_count, idf_table):
    word_stat = {}
    word_count = 0
    response = {}

    for line in clean_lines(lines):
        for w in tagger.normalize(line):
            if w not in word_stat:
                word_stat[w] = 0
            word_stat[w] += 1
            word_count += 1
    word_count = float(word_count)

    tf_idf = {}
    for word, count in word_stat.iteritems():
        tf = math.log(1 + count / word_count)
        idf = math.log(idf_doc_count)
        if word in idf_table:
            idf = math.log(idf_doc_count / idf_table[word])
        tf_idf[word] = tf * idf

    sorted_terms = sorted(word_stat.keys(), key=lambda x: -tf_idf[x])
    keywords = sorted_terms[:2] + [t for t in  sorted_terms[2:] if tf_idf[t] >= 0.2]
    response['keywords'] = keywords
    response['scores'] = [tf_idf[k] for k in keywords]
    return response



if __name__ == "__main__":
    if sys.stdout.encoding != 'UTF-8':
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout, 'strict')
    tagger = Morphodita("/net/projects/morphodita/models/czech-morfflex-pdt-131112/czech-morfflex-pdt-131112-pos_only-raw_lemmas.tagger")

    f_idf = open("idf_table.pickle", 'rb')
    idf_doc_count = float(pickle.load(f_idf))
    idf_table = pickle.load(f_idf)
    f_idf.close()

    base_dir = sys.argv[1]
    for d in os.listdir(base_dir):
        dir_path = os.path.join(base_dir, d)
        if not os.path.isdir(dir_path):
            continue
        word_stat = {}
        word_count = 0
        for f in os.listdir(dir_path):
            if not f.endswith(".txt"):
                continue
            file_path = os.path.join(dir_path, f)
            for t in texts_from_file(file_path):
                for w in tagger.normalize(t):
                    if w not in word_stat:
                        word_stat[w] = 0
                    word_stat[w] += 1
                    word_count += 1
        word_count = float(word_count)
        # the word counts are computed now, lets compute the tf-idf score
        tf_idf = {}
        for word, count in word_stat.iteritems():
            tf = math.log(1 + count / word_count)
            idf = math.log(idf_doc_count)
            if word in idf_table:
                idf = math.log(idf_doc_count / idf_table[word])
            tf_idf[word] = tf * idf

        sorted_terms = sorted(word_stat.keys(), key=lambda x: -tf_idf[x])
        keywords = sorted_terms[:2] + [t for t in  sorted_terms[2:] if tf_idf[t] >= 0.2]
        term_strings = [u"{} ({:.3f})".format(t, tf_idf[t]) for t in keywords]

        print u"{}:\t{}".format(d, u", ".join(term_strings[:10]))
