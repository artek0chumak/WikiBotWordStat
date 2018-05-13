# -*- coding: utf-8 -*-
"""
Обучение модели для генерации текста на основоне других текстов.
Используйте -h для вызова справки.
"""
import argparse
import os
import re
import sys
import model


def gen_token(files):
    """
    Генератор слов из файлов текстов
    :param files: Список путей к файлам
    :type files: generator
    :return: Слово из файла
    :rtype: str
    """
    alpha = '[а-яА-Я]+|[a-zA-Z]+'

    r = re.compile(alpha)
    for file in files:
        for line in file:
            for token in r.findall(line):
                yield token


def gen_lines(file, lc):
    """
    Генератор строк из файла
    :param file: Путь к файлу
    :param lc: Флаг на использование lower
    :type file: file object
    :type lc: bool
    :return: Строку из файла
    :rtype: str
    """
    for line in file:
        if lc:
            yield line.lower()
        else:
            yield line


def open_files(dest_file, lc):
    """
    Созданиие списка строк
    :param dest_file: Путь к файлу
    :param lc: Флаг на использование lower
    :type dest_file: str
    :type lc: bool
    :return: Список файлов, т.е. список строк
    :rtype: list
    """
    if dest_file is None:
        yield gen_lines(sys.stdin, lc)
    else:
        for root, dirs, files in os.walk(dest_file):
            for file in files:
                if file.endswith('.txt'):
                    with open(os.path.join(root, file), 'r') as f:
                        yield gen_lines(f, lc)


def gen_ngramms(token, n):
    """
    Генерация n-грамм
    :param token: Генератор токена
    :param n: Количество слов в n-грамме
    :type token: generator
    :type n: int
    :return: Список из слов
    :rtype: list
    """
    it_token = iter(token)
    t = [next(it_token) for _ in range(n - 1)]
    for ti in token:
        yield t + [ti]
        t = t[1:] + [ti]


def main(args):
    """
    Главная функция
    :param args: Аргументы запуска обучения
    :type args: class
    :return: None
    """
    files = open_files(args.input_dir, args.lc)
    token = gen_token(files)
    ngramms = gen_ngramms(token, args.ngramms)
    model.train_model(ngramms, args.model, args.update)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Train model to generate texts.', prog='train.py')
    parser.add_argument('--lc', action='store_true',
                        help='apply lower_case() to texts')
    parser.add_argument('--input-dir', action='store',
                        help='destination to texts. If it isn'
                             '\'t set, uses texts from stdin')
    parser.add_argument('--model', action='store',
                        help='destination to model file')
    parser.add_argument('--ngramms', action='store', default=2, type=int,
                        help='number of using words in one token')
    parser.add_argument('--update', action='store_true',
                        help='update model')
    main(parser.parse_args())
