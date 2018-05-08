import parser
import pandas as pd
import pymorphy2
import train
import model
import generate
import re


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

    def get_texts(self):
        """
        Получение слов с сайта
        :return: None
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

    def write(self, N):
        """
        Написание текста
        :param N: Количество слов в текста
        :return: Текст, сгенерированный из текстов сайта
        """
        model_ngramms = model.load_model('model_{0}'.format(
            re.findall(r'\.[\w]\.', self.url)[0]))
        text_gen = generate.generate_text(model_ngramms, N, None)
        return " ".join(text_gen)
