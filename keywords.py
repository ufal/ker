#!/usr/bin/env python3

import re
import math

STOPWORDS = {
    "en": {'i', 'further', 'had', 'isn', 'o', 'haven', 'can',
           'themselves', 'won', 'myself', 'why', 'between', 'don', 'didn',
           'such', 'ourselves', 'hasn', 'on', 'll', 'your', 'how', 'when',
           'with', 'what', 'himself', 'they', 'own', "should've", 'aren', 'up',
           "it's", 'through', 'any', 'its', 'few', 'all', 'ain', 'above',
           'she', 'if', 'are', 'm', 'do', 'having', 'more', "migh tn't",
           "won't", 'because', 'an', 'not', 'he', 'to', 'me', "hadn't",
           'while', 'shouldn', 'their', 'his', 'just', "didn't", 'being',
           'into', 're', 'each', "don't", 'him', 'by', 'it', 'a bout', 'am',
           'will', 'wasn', 's', 've', 'then', "that'll", 'was', 'were', 'once',
           'you', 'too', 'the', "shouldn't", "she's", 'hers', 'of', 'very',
           "weren't", 'ours', 'theirs', 'both', 'below', 'at', 'over',
           'herself', 'and', 'or', 'as', "haven't", 'shan', "isn't",
           'yourselves', "aren't", 'did', 'be', 'before', 'that', 'out',
           'than', 'is', 'which', 'whom', 'no', 't his', 'some', "you'd",
           'only', 'yours', "shan't", 'we', 'in', 'again', "mustn't", 'so',
           "wasn't", 'same', 'd', 'hadn', 'mustn', 'does', 'couldn', 'wouldn',
           'here', 'been', 'until', 'n eedn', 'for', 'them', 'y', 'mightn',
           "wouldn't", "needn't", 'nor', 'but', 'these', 'after', "you've",
           'our', 'during', 'those', 'most', 'against', 'ma', 'there',
           'should', 'my', "does n't", 'doesn', "couldn't", 'itself', 'where',
           "hasn't", 'now', 'yourself', "you're", 'off', 'doing', 'have',
           'under', 'from', 'down', 'who', "you'll", 'has', 'her', 'other',
           'weren', 't', 'a'},

    "cs": {'ačkoli', 'ahoj', 'ale', 'anebo', 'ano', 'asi', 'aspoň',
           'během', 'bez', 'beze', 'blízko', 'bohužel', 'brzo', 'bude',
           'budeme', 'budeš', 'budete', 'budou', 'budu', 'byl', 'byla', 'byli',
           'bylo', 'byly', 'bys', 'čau', 'chce', 'chceme', 'chceš', 'chcete',
           'chci', 'chtějí', 'chtít', 'chut', 'chuti', 'co', 'čtrnáct',
           'čtyři', 'dál', 'dále', 'daleko', 'děkovat', 'děkujeme', 'děkuji',
           'den', 'deset', 'devatenáct', 'devět', 'do', 'dobrý', 'docela',
           'dva', 'dvacet', 'dvanáct', 'dvě', 'hodně', 'já', 'jak', 'jde',
           'je', 'jeden', 'jedenáct', 'jedna', 'jedno', 'jednou', 'jedou',
           'jeho', 'její', 'jejich', 'jemu', 'jen', 'jenom', 'ještě', 'jestli',
           'jestliže', 'jí', 'jich', 'jím', 'jimi', 'jinak', 'jsem', 'jsi',
           'jsme', 'jsou', 'jste', 'kam', 'kde', 'kdo', 'kdy', 'když', 'ke',
           'kolik', 'kromě', 'která', 'které', 'kteří', 'který', 'kvůli', 'má',
           'mají', 'málo', 'mám', 'máme', 'máš', 'máte', 'mé', 'mě', 'mezi',
           'mí', 'mít', 'mně', 'mnou', 'moc', 'mohl', 'mohou', 'moje', 'moji',
           'možná', 'můj', 'musí', 'může', 'my', 'na', 'nad', 'nade', 'nám',
           'námi', 'naproti', 'nás', 'náš', 'naše', 'naši', 'ne', 'ně', 'nebo',
           'nebyl', 'nebyla', 'nebyli', 'nebyly', 'něco', 'nedělá', 'nedělají',
           'nedělám', 'neděláme', 'neděláš', 'neděláte', 'nějak', 'nejsi',
           'někde', 'někdo', 'nemají', 'nemáme', 'nemáte', 'neměl', 'němu',
           'není', 'nestačí', 'nevadí', 'než', 'nic', 'nich', 'ním', 'nimi',
           'nula', 'od', 'ode', 'on', 'ona', 'oni', 'ono', 'ony', 'osm',
           'osmnáct', 'pak', 'patnáct', 'pět', 'po', 'pořád', 'potom', 'pozdě',
           'před', 'přes', 'přese', 'pro', 'proč', 'prosím', 'prostě', 'proti',
           'protože', 'rovně', 'se', 'sedm', 'sedmnáct', 'šest', 'šestnáct',
           'skoro', 'smějí', 'smí', 'snad', 'spolu', 'sta', 'sté', 'sto', 'ta',
           'tady', 'tak', 'takhle', 'taky', 'tam', 'tamhle', 'tamhleto',
           'tamto', 'tě', 'tebe', 'tebou', 'teď', 'tedy', 'ten', 'ti', 'tisíc',
           'tisíce', 'to', 'tobě', 'tohle', 'toto', 'třeba', 'tři', 'třináct',
           'trošku', 'tvá', 'tvé', 'tvoje', 'tvůj', 'ty', 'určitě', 'už',
           'vám', 'vámi', 'vás', 'váš', 'vaše', 'vaši', 've', 'večer', 'vedle',
           'vlastně', 'všechno', 'všichni', 'vůbec', 'vy', 'vždy', 'za', 'zač',
           'zatímco', 'ze', 'že', 'aby', 'aj', 'ani', 'az', 'budem', 'budes',
           'by', 'byt', 'ci', 'clanek', 'clanku', 'clanky', 'coz', 'cz',
           'dalsi', 'design', 'dnes', 'email', 'ho', 'jako', 'jej', 'jeji',
           'jeste', 'ji', 'jine', 'jiz', 'jses', 'kdyz', 'ktera', 'ktere',
           'kteri', 'kterou', 'ktery', 'ma', 'mate', 'mi', 'mit', 'muj',
           'muze', 'nam', 'napiste', 'nas', 'nasi', 'nejsou', 'neni', 'nez',
           'nove', 'novy', 'pod', 'podle', 'pokud', 'pouze', 'prave', 'pred',
           'pres', 'pri', 'proc', 'proto', 'protoze', 'prvni', 'pta', 're',
           'si', 'strana', 'sve', 'svych', 'svym', 'svymi', 'take', 'takze',
           'tato', 'tema', 'tento', 'teto', 'tim', 'timto', 'tipy', 'toho',
           'tohoto', 'tom', 'tomto', 'tomuto', 'tu', 'tuto', 'tyto', 'uz',
           'vam', 'vas', 'vase', 'vice', 'vsak', 'zda', 'zde', 'zpet',
           'zpravy', 'a', 'aniž', 'až', 'být', 'což', 'či', 'článek', 'článku',
           'články', 'další', 'i', 'jenž', 'jiné', 'již', 'jseš', 'jšte', 'k',
           'každý', 'kteři', 'ku', 'me', 'ná', 'napište', 'nechť', 'ní',
           'nové', 'nový', 'o', 'práve', 'první', 'přede', 'při', 's', 'sice',
           'své', 'svůj', 'svých', 'svým', 'svými', 'také', 'takže', 'te',
           'těma', 'této', 'tím', 'tímto', 'u', 'v', 'více', 'však', 'všechen',
           'z', 'zpět', 'zprávy', 'odstavec', 'kapitola', 'obsah', 'část',
           'cvičení', 'metoda', 'druh', 'rovnice', 'rejstřík', 'literatura',
           'seznam', 'základ', 'příklad', 'stanovení', 'definice', 'výpočet',
           'csc', 'prof', 'ing', 'doc', 'bibilografie', 'příloha', 'index',
           'bibliography', 'appendix', 'preface', 'summary', 'postup', 'úvod',
           'poznámka', 'závěr', 'úloha', 'zadání', 'procvičení'}}


def clean_lines(lines):
    """
    Returns the text that are present in a file after removing formating
    marks

    :param lines: List of plain text lines
    :type lines: list[str]
    """
    for line in lines:
        line = line.strip()
        line = re.sub("[[:space:]]+\\([^(]*\\)", "", line).strip()
        line = re.sub(r"[0-9]+(\.[0-9]+)*\.?[[:space:]]*", "", line).strip()
        line = re.sub(
            r"[[:space:]]*((\.+)|([[:space:]]+))[[:space:]]*[0-9]*$",
            "",
            line).strip()
        if line:
            yield line


class Morphodita(object):
    """
    A wrapper class for stuff needed fro working with Moprhodita.
    """

    def __init__(self, model_file, language):
        """
        Instantiates Morphodita from a provided model file.

        :param model_file: Path to the model file,
        :type model_file: str
        """
        from ufal.morphodita import Tagger, Forms, TaggedLemmas, TokenRanges

        self.language = language
        assert language in ['cs', 'en']

        self.tagger = Tagger.load(model_file)
        self.forms = Forms()
        self.lemmas = TaggedLemmas()
        self.tokens = TokenRanges()
        self.tokenizer = self.tagger.newTokenizer()

    def normalize(self, text):
        """
        Returns lematized nouns and adjectives from a provided text.

        :param text: Text to be processed
        :type text: str
        """
        self.tokenizer.setText(text)
        lemmas = []
        while self.tokenizer.nextSentence(self.forms, self.tokens):
            self.tagger.tag(self.forms, self.lemmas)
            lemmas += [l.lemma.lower() for l in self.lemmas if (l.tag == 'NN' or l.tag == 'AA')
                       and len(l.lemma) > 2 and l.lemma not in STOPWORDS[self.language]]
        return lemmas, len(self.lemmas)


def get_keywords(
        lines,
        tagger,
        idf_doc_count,
        idf_table,
        threshold,
        maximum_words):
    """
    Finds keywords in the provided lines of text using the tf-idf measure.

    :param lines: Preprocessed lines of text
    :type lines: list[str]

    :param tagger: Loaded Morphodita model for normalization of the text
    :type tagger: Morphodita

    :param idf_doc_count: Number of documents used for creating the idf table
    :type idf_doc_count: int

    :param idf_table: Precomputed IDF table.
    :type idf_table: dict

    :param threshold: Minimum score that is acceptable for a keyword.

    :param maximum_words: Maximum number of words to be returned.

    """
    word_stat = {}
    word_count = 0
    response = {}

    morphodita_calls = 0
    for line in clean_lines(lines):
        norm_words, line_call_count = tagger.normalize(line)
        morphodita_calls += line_call_count
        for w in norm_words:
            if w not in word_stat:
                word_stat[w] = 0
            word_stat[w] += 1
            word_count += 1
    word_count = float(word_count)

    tf_idf = {}
    for word, count in word_stat.items():
        tf = math.log(1 + count / word_count)
        idf = math.log(idf_doc_count)
        if word in idf_table:
            idf = math.log(idf_doc_count / idf_table[word])
        tf_idf[word] = tf * idf

    sorted_terms = sorted(word_stat.keys(), key=lambda x: -tf_idf[x])
    keywords = (sorted_terms[:2] + [t for t in sorted_terms[2:]
                if tf_idf[t] >= threshold])[:maximum_words]
    response['keywords'] = keywords
    response['keyword_scores'] = [tf_idf[k] for k in keywords]
    response['morphodita_calls'] = morphodita_calls
    return response
