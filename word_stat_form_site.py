"""
Библиотека для работы со статистикой слов из сайта.
"""
import parser
import pandas as pd
# import pymorphy2
import train
import model
import generate
import re
import collections
import numpy
import json
import os
import matplotlib.pyplot as plt
from wordcloud import WordCloud


class WordStatFromSite:
    def __init__(self, url, depth, chat_id):
        """
        Инициализация объекта для поиска данных с сайта.
        :param url: url первоначального сайта
        :type url: str
        :param depth: глубина поиска
        :type depth: int
        """
        self.url = url
        self.depth = depth
        self.chat_id = chat_id

        self.url_name = re.findall(r'\.[\w]\.', self.url)[0]
        # self.morph = pymorphy2.MorphAnalyzer()

        self.work_dir = 'chat_{0}'.format(self.chat_id)

        # Расположение файлов с текстом, моделью для генерации текста
        #  и статистикой
        self.dst_texts = os.path.join(self.work_dir,
                                      'texts_{0}.txt'.format(self.url_name))
        self.dst_words_stat = os.path.join(self.work_dir,
                                           'word_stat_{0}.csv'.format(
                                               self.url_name))
        self.dst_bigramms = os.path.join(self.work_dir,
                                         'bigramms_{0}.json'.format(
                                             self.url_name))
        # Расположение слова в предложении, place-in-sentence
        self.dst_PIS = os.path.join(self.work_dir,
                                    'PIS_{0}.json'.format(self.url_name))
        self.dst_model = os.path.join(self.work_dir,
                                      'model_{0}'.format(self.url_name))

        urls = set()
        urls.add((self.url, 0))
        used_urls = set()

        with open(self.dst_texts, 'w') as texts:
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
        with open(self.dst_texts, 'w') as texts:
            token = train.gen_token(train.gen_lines(texts, False))
            ngramms = train.gen_ngramms(token, 3)
            model.train_model(ngramms, self.dst_model, False)

    def write(self, n):
        """
        Написание текста
        :param n: Количество слов в текста
        :return: Текст, сгенерированный из текстов сайта
        """
        model_ngramms = model.load_model(self.dst_model)
        text_gen = generate.generate_text(model_ngramms, n, None)
        return " ".join(text_gen)

    def gen_stat(self):
        """
        Создание статистики для текста
        """
        word_freq = collections.Counter()
        place_in_sent = {}
        with open(self.dst_texts, 'w') as texts:
            for line in texts:
                word_freq.update(
                    [_.lower() for _ in re.findall(r'[\w]+', line)])

                n = 1
                for sent in line.split('.'):
                    for word in re.findall(r'[\w]+', sent):
                        if place_in_sent.get(word.lower()) is None:
                            place_in_sent[word.lower()] = list()
                        place_in_sent[word.lower()].append(n)
                        n += 1

        token = train.gen_token(train.gen_lines(texts, False))

        words_stat = {'length': pd.Series(
            map(len, word_freq.keys()), index=word_freq.keys()),
            'frequency': pd.Series(word_freq)}
        # Возможно использованиие pymorph2 для анализа текста. Если останется
        # время
        # lang_morph_data = ['POS', 'animacy', 'aspect', 'case', 'gender',
        #                    'involvement', 'mood', 'number', 'person', 'tense',
        #                    'transitivity', 'voice']
        # pre_words_stat.update({t: pd.Series(
        #     map(lambda x: self.morph.parse(x)[0].tag.__getattribute__(t),
        #         word_freq.keys()), index=word_freq.keys()) for t in
        #     lang_morph_data})

        with open(self.dst_words_stat, 'w') as file:
            pd.DataFrame(words_stat).to_csv(file)
        with open(self.dst_bigramms, 'w') as file:
            json.dump([_ for _ in train.gen_ngramms(token, 2)], file)
        with open(self.dst_PIS, 'w') as file:
            json.dump({word: numpy.array(place_in_sent[word]) for
                       word in place_in_sent.keys()}, file)

    def top(self, n, order):
        """
        Вывод топа слов
        :param n: Количество слов в топе
        :type n: int
        :param order: Порядок слов
        :type order: str
        :return: Список слов в топе
        :rtype: list
        """
        with open(self.dst_words_stat, 'r') as file:
            word_stat = pd.DataFrame.from_csv(file)

        avg_freq = word_stat['frequency'].mean()
        std_freq = word_stat['frequency'].std()

        temp_table = word_stat[
            (word_stat['frequency'] < avg_freq + 3 * std_freq) & (
                    word_stat['frequency'] > avg_freq - 3 * std_freq)]

        return list(
            temp_table.sort_values('frequency', ascending=order == 'asc').head(
                n).index)

    def stop_words(self):
        """
        Вывод слов-выбросов
        :return: Список слов-выбросов
        :rtype: list
        """
        with open(self.dst_words_stat, 'r') as file:
            word_stat = pd.DataFrame.from_csv(file)

        avg_freq = word_stat['frequency'].mean()
        std_freq = word_stat['frequency'].std()

        temp_table = word_stat[
            (word_stat['frequency'] > avg_freq + 3 * std_freq) | (
                    word_stat['frequency'] < avg_freq - 3 * std_freq)]

        return list(temp_table.index)

    def word_cloud(self, color):
        """
        Создание облака слов. Возвращает местоположение полученного фото.
        :param color: Используемая цветовая карта
        :type color: str
        :return: Местоположение фото
        :rtype: str
        """
        with open(self.dst_texts, 'w') as texts:
            text = texts.read()
            wordcloud = WordCloud(colormap=color).generate(text)
            dst_photo = os.path.join(self.work_dir,
                                     'wordcloud_{0}.png'.format(self.url_name))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.imsave(dst_photo, format='png')
            return dst_photo

    def describe(self):
        """
        Статистика по тексту
        :return: Статистика по частоте и длине в виде словаря
        :rtype: dict
        """
        with open(self.dst_words_stat, 'r') as file:
            describe = dict(pd.DataFrame.from_csv(file).describe())
            return {i: dict(describe[i]) for i in describe}

    def describe_word(self, word):
        """
        Статистика использования слова в тексте
        :param word: Слово
        :type word: str
        :return: Словарь со статистикой
        :rtype: dict
        """
        word = word.lower()
        with open(self.dst_words_stat, 'r') as file:
            words_stat = pd.DataFrame.from_csv(file)
        with open(self.dst_bigramms, 'r') as file:
            bigramms = json.load(file)
        with open(self.dst_PIS, 'r') as file:
            PIS_word = json.load(file).get(word)
            # Если такого слова нет, то выводится пустая статистика
            if PIS_word is None:
                PIS_word = numpy.array()

        neighbours = collections.Counter(
            [i[0] for i in bigramms if i[1] == word])
        neighbours.update([i[1] for i in bigramms if i[0] == word])

        word_stat = words_stat.loc(word)
        stat_by_word = {'frequency': word_stat['frequency'],
                        'place_by_freq': words_stat[
                            'frequency' > word_stat['frequency']].shape[0],
                        'max_neighbour': neighbours.most_common(),
                        'mean_PIS': PIS_word.mean(), 'std_PIS': PIS_word.std(),
                        'min_PIS': PIS_word.min(), 'max_PIS': PIS_word.max()}

        return stat_by_word
