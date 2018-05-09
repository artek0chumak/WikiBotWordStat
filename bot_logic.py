import parser
import pandas as pd
# import pymorphy2
import train
import model
import generate
import re
import collections
import numpy
import matplotlib.pyplot as plt


class WordStatFromSite:
    def __init__(self, url, depth):
        """
        Инициализация объекта для поиска данных с сайта.
        :param url: url первоначального сайта
        :type url: str
        :param depth: глубина поиска
        :type depth: int
        """
        self.url = url
        self.depth = depth
        # self.morph = pymorphy2.MorphAnalyzer()
        # Данные для статистики
        self.word_stat = None
        self.bigramms = None
        self.place_in_sent = None

    def get_texts(self):
        """
        Получение слов с сайта
        """
        urls = set()
        urls.add((self.url, 0))
        used_urls = set()

        with open('texts.txt', 'w') as texts:
            for url in urls.difference(used_urls):
                used_urls.add(url)
                parser_site = parser.UrlParser(url[0])
                text = ' '.join([_ for _ in parser_site.find_paragraphs()])
                texts.write(text)
                if url[1] < self.depth:
                    urls.update([(href, 0) for href in
                                 parser_site.find_references() if
                                 href is not None])

    def train_writer(self):
        """
        Обучение модели для генерации текста. Создает файл модели.
        """
        with open('texts.txt', 'r') as texts:
            token = train.gen_token(train.gen_lines(texts, False))
            ngramms = train.gen_ngramms(token, 3)
            model.train_model(ngramms, 'model_{0}'.format(
                re.findall(r'\.[\w]\.', self.url)[0]), False)

    def write(self, n):
        """
        Написание текста
        :param n: Количество слов в текста
        :return: Текст, сгенерированный из текстов сайта
        """
        model_ngramms = model.load_model('model_{0}'.format(
            re.findall(r'\.[\w]\.', self.url)[0]))
        text_gen = generate.generate_text(model_ngramms, n, None)
        return " ".join(text_gen)

    def gen_stat(self):
        """
        Создание статистики для текста
        """
        word_freq = collections.Counter()
        temp_place_in_sent = {}
        with open('texts.txt', 'r') as texts:
            for line in texts:
                word_freq.update(
                    [_.lower() for _ in re.findall(r'[\w]+', line)])

                n = 1
                for sent in line.split('.'):
                    for word in re.findall(r'[\w]+', sent):
                        if temp_place_in_sent.get(word.lower()) is None:
                            temp_place_in_sent[word.lower()] = list()
                        temp_place_in_sent[word.lower()].append(n)
                        n += 1

        self.place_in_sent = {word: numpy.array(temp_place_in_sent[word]) for
                              word in temp_place_in_sent.keys()}

        token = train.gen_token(train.gen_lines(texts, False))
        self.bigramms = [_ for _ in train.gen_ngramms(token, 2)]

        pre_words_stat = {'length': pd.Series(
            map(len, word_freq.keys()), index=word_freq.keys()),
            'frequency': pd.Series(word_freq)}
        # Возможно использованиие pymorph2 для анализа текста
        # lang_morph_data = ['POS', 'animacy', 'aspect', 'case', 'gender',
        #                    'involvement', 'mood', 'number', 'person', 'tense',
        #                    'transitivity', 'voice']
        # pre_words_stat.update({t: pd.Series(
        #     map(lambda x: self.morph.parse(x)[0].tag.__getattribute__(t),
        #         word_freq.keys()), index=word_freq.keys()) for t in
        #     lang_morph_data})

        self.word_stat = pd.DataFrame(pre_words_stat)

    def top(self, n, order):
        """
        Генерация топа слов
        :param n: Количество слов в топе
        :type n: int
        :param order: Порядок слов
        :type order: str
        :return: Список слов в топе
        :rtype: list
        """
        avg_freq = self.word_stat['frequency'].mean()
        std_freq = self.word_stat['frequency'].std()

        temp_table = self.word_stat[
            (self.word_stat['frequency'] < avg_freq + 3 * std_freq) & (
                    self.word_stat['frequency'] > avg_freq - 3 * std_freq)]

        return list(
            temp_table.sort_values('frequency', ascending=order == 'asc').head(
                n).index)
