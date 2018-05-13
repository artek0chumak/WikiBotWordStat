# -*- coding: utf-8 -*-
"""
Генератор текста из модели, полученной обучением с помощью train.py.
Используйте -h для вызова справки.
"""
import argparse
import random
import model


def weighted_choices(choices):
    """
    Куммулятивное распределение
    :param choices: Последовательность слов и их частоты
    :type choices: list or tuple
    :return: Выбранное слово
    :rtype: str or None
    """
    # c - слово, w - вес
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w

    return None


def first_words(model_ngramm, start, start_words):
    """
    Поиск первых слов
    :param model_ngramm: Модель текстов
    :param start: Начальное слово
    :param start_words: Список слов, с которых может начинаться предложения
    :type model_ngramm: Counter
    :type start: str
    :type start_words: tuple
    :return: Список из n слов
    :rtype: list
    """

    if start is None:
        start = random.choice(start_words)
    # Если seed был None, то мы после выбрали слово, которое точно
    # находится в модели
    elif start not in start_words:
        raise KeyError('Данного слова нет в модели')

    # Поиск первых n-1 слов среди n-грамм, используя
    # seed в качетсве первого
    ngramm = [start] + list(random.choice(tuple(i[1:] for i in model_ngramm
                                                if i[0] == start)))
    # Если не нашлись такие n-граммы, то берём любые
    if len(ngramm) == 1:
        ngramm += random.choice(tuple(i[1:] for i in model_ngramm))

    return ngramm


def next_words(model_ngramm, ngramm, start_words):
    """
    Нахождение следующей nграммы
    :param model_ngramm: Модель текстов
    :param ngramm: Список слов
    :param start_words: Список слов, с которых может начинаться предложения
    :type model_ngramm: Counter
    :type ngramm: list
    :type start_words: tuple
    :return: Список слов
    :rtype: list
    """
    temp = weighted_choices(tuple((i[-1], model_ngramm[i])
                                  for i in model_ngramm
                                  if list(i[:-1]) == ngramm[1:]))

    if temp is None:
        # Выбор нового слова, если
        # не удалось найти подходящий по последним
        temp = random.choice(start_words)

    # Удаляем первое слово, так как оно больше нам не нужно
    ngramm = ngramm[1:] + [temp]

    return ngramm


def generate_text(model_ngramm, length, seed):
    """
    Генерация текста
    :param model_ngramm: Модель текстов
    :param length: Длина текста в словах
    :param seed: Начальное слово
    :type model_ngramm: dict or Counter
    :type length: int
    :type seed: str
    :return: Генератор слов
    :rtype: generator
    """
    # Слова, с которых могут начинться предложения.
    start_words = tuple(i[0] for i in model_ngramm)

    # Находим первые слова для текста
    text_gen = first_words(model_ngramm, seed, start_words)

    yield text_gen[0]

    while length - 1 > 0:
        # Находим последующие слова
        text_gen = next_words(model_ngramm, text_gen, start_words)

        length -= 1

        yield text_gen[0]


def save_text(text, text_dest):
    """
    Сохраняет текст в файл
    :param text: Текст
    :param text_dest: Располжение файла текста
    :type text: str
    :type text_dest: str
    :return: None
    """
    with open(text_dest, 'w') as f:
        f.write(text)


def main(args):
    """
    Главная функция
    :param args: Аргументы запуска генератора
    :type args: Class
    :return: None
    """
    model_ngramm = model.load_model(args.model)
    text_gen = generate_text(model_ngramm, args.length, args.seed)
    text = ' '.join(text_gen)

    if args.output is None:
        print(text)
    else:
        save_text(text, args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate text using model.',
                                     prog='generate.py')
    parser.add_argument('--model', action='store',
                        help='destination to model file')
    parser.add_argument('--seed', action='store', help='set starting word')
    parser.add_argument('--length', action='store', type=int,
                        help='length of generated text')
    parser.add_argument('--output', action='store',
                        help='destination to output file.'
                             ' If it isn\'t set, uses stdout')
    main(parser.parse_args())
