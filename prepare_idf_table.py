#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import cPickle as pickle
import bz2
import sys, os
from process import Morphodita

def main(wiki_root, morphodita_model_file, output):
    tagger = Morphodita(morphodita_model_file)
    word_document_counts = {}
    document_count = 0

    current_document_words = {}
    for d in os.listdir(wiki_root):
        dir_path = os.path.join(wiki_root, d)
        if not os.path.isdir(dir_path):
            continue
        print "Processing "+dir_path
        for f in os.listdir(dir_path):
            file_path = os.path.join(dir_path, f)
            f_wiki = None
            if f.endswith(".bz2"):
                f_wiki = bz2.BZ2File(file_path, 'r')
            else:
                f_wiki = open(file_path, 'r')
            try:
                for line in f_wiki:
                    if line.startswith('</doc'):
                        current_document_words = {}
                        document_count += 1
                    if not line.startswith('<'):
                        words = tagger.normalize(line.strip())
                        for w in words:
                            if w not in current_document_words:
                                current_document_words[w] = 1
                                if w not in word_document_counts:
                                    word_document_counts[w] = 1
                                else:
                                    word_document_counts[w] += 1
            except:
                pass
            finally:
                f_wiki.close()

    f_idf = open(output, 'wb')
    pickle.dump(document_count, f_idf)
    pickle.dump(word_document_counts, f_idf)
    f_idf.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Prepares the IDF model pro preprocessed wikipedia articles')
    parser.add_argument("--morphodita", help="Path to Morphodita model.")
    parser.add_argument("--wiki", help="Path to root directory of preprocessed wikipedia.")
    parser.add_argument("--output", help="Output file.")
    args = parser.parse_args()

    main(args.wiki, args.morphodita, args.output)

