"""
Файл для парсинга сайта
"""
import requests
from lxml import etree
from io import StringIO


class UrlParser:
    """
    Парсер сайта, возвращает текст из <p> и ссылки из сайта.
    """
    def __init__(self, url):
        """
        :param url: Ссылка на сайт
        :rtype: str
        """
        responce = requests.get(url)
        html = responce.text
        parser = etree.HTMLParser()

        self.tree = etree.parse(StringIO(html), parser)

    def find_paragraphs(self):
        """
        Поиск всех данных из сайта с тэгом <p></p>
        :return: Генератор данных
        :rtype: generator
        """
        for p in self.tree.xpath('//p'):
            yield p.text
        for pre in self.tree.xpath('//pre'):
            yield pre.text

    def find_references(self):
        """
        Поиск ссылок в сайте
        :return: Генератор данных
        :rtype: generator
        """
        for href in self.tree.xpath('//a'):
            yield href.attrib.get('href', None)
