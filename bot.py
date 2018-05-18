"""
Скрипт работы телеграм бота
"""
import telebot
import re
# Файл с токеном для запуска бота
import requests
import config
from word_stat_form_site import WordStatFromSite

ip = 'mcvie.reconnect.rocks'
port = '1080'
login = 'telegram'
password = 'telegram'
#
# telebot.apihelper.proxy = {
#   'https': 'socks5://{}:{}@{}:{}'.format(login, password, ip, port)
# }

bot = telebot.TeleBot(config.token)

currents_chat_url = {}
# Регулярное выражения для поиска url в тексте
url_reg = r'(?:(?:https?|ftp):\/\/|\b(?:[a-z\d]+\.))(?:(?:[^\s()<>]+|\((?:' \
          r'[^\s()<>]+|(?:\([^\s()<>]+\)))?\))+(?:\((?:[^\s()<>]+|(?:\(?:[^' \
          r'\s()<>]+\)))?\)|[^\s`!()\[\]{};:\'.,<>?«»“”‘’]))?'


def has_url(function):
    """
    Есть ли у пользователя сайт для анализа
    """
    def wrapper(message, *args):
        if currents_chat_url.get(message.chat.id, None) is None:
            bot.send_message(message.chat.id, 'Нет текста для анализа')
        else:
            function(message, *args)

    return wrapper


def print_message_deb(function):
    def wrapper(message, *args):
        print('{0}: {1}'.format(message.chat.id, message.text))
        function(message, *args)

    return wrapper


@bot.message_handler(commands=['start'])
@print_message_deb
def start_bot(message):
    bot.send_message(message.chat.id, 'Привет! Чтобы узнать, как '
                                      'меня использовать, напиши /help.')


@bot.message_handler(regexp=url_reg + r' [\d]+')
@print_message_deb
def get_url(message):
    """
    Получение ссылки
    """
    url = re.findall(url_reg, message.text)[0]
    if url[:4] != 'http':
        url = 'http://' + url
    depth = int(re.findall(r'[\d]+', message.text)[-1])
    bot.send_message(message.chat.id, 'Находим все тексты. Переход по ссылкам '
                                      'требует времени, пожалуйста, подождите '
                                      'сообщение о завершении.')
    if depth > 5:
        bot.send_message(message.chat.id, 'Слишком большая глубина поиска.')
    else:
        try:
            currents_chat_url[message.chat.id] = \
                WordStatFromSite(url, depth, message.chat.id)
            currents_chat_url[message.chat.id].get_texts_from_url(
                bot.send_message)
            bot.send_message(message.chat.id,
                             'Начинаем анализировать тексты...')
            currents_chat_url[message.chat.id].train_writer()
            currents_chat_url[message.chat.id].gen_stat()
            bot.send_message(message.chat.id, 'Статистика получена.')
        except requests.exceptions.ConnectionError:
            bot.send_message(message.chat.id, 'Не удалось пройти по сайтам. '
                                              'Попробуйте позже')


@bot.message_handler(commands=['help'])
@print_message_deb
def show_help(message):
    """
    Показать комманды пользователю
    """
    text = '/start - начать использовать бота\n' \
           '/help - вывести этот текст\n\n' \
           'http://www.ru.wikipedia.com N - пример запроса сайта для анализа.' \
           ' N - глубина перехода по ссылкам. N = 1 - только переданной ' \
           'страницы. Ограничение на глубину - 5.\n\n' \
           'write N - написать N слов, используя трёхграммную модель\n' \
           'top N asc|desc - вывести топ слов по частоте использование. ' \
           'N - число слов, asc - в прямом порядке, desc - в обратном\n' \
           'stop word - вывести слова выбросы\n' \
           'word cloud COLORMAP - создать облако слов\n' \
           'describe - статистика по использованию слов\n' \
           'describe WORD - вывести статистику по использованию этого слова\n'
    bot.send_message(message.chat.id, text)


@bot.message_handler(regexp='write [\d]+')
@has_url
@print_message_deb
def write_n(message):
    """
    Написать текст по текстам пользователя
    """
    list_m = message.text.split()
    n = int(re.findall(r'[\d]+', message.text)[0])
    text = currents_chat_url[message.chat.id].write(n)
    bot.send_message(message.chat.id, text)


@bot.message_handler(regexp='top [\d]+(| asc| desc)')
@has_url
@print_message_deb
def show_top_n(message):
    """
    Показать топ слов
    """
    list_m = message.text.split()
    n = int(re.findall(r'[\d]+', message.text)[0])
    order = 'asc' if len(list_m) < 3 else list_m[2]
    words = currents_chat_url[message.chat.id].top(n, order)
    bot.send_message(message.chat.id, '\n'.join(
        ['{0}. {1}'.format(p + 1, w) for p, w in
         zip(range(len(words)), words)]))


@bot.message_handler(regexp='stop word')
@has_url
@print_message_deb
def stop_word(message):
    """
    Показать слова выбросы
    """
    words = currents_chat_url[message.chat.id].stop_words()
    bot.send_message(message.chat.id, ', '.join(
        ['{0}'.format(w) for w in words]))


@bot.message_handler(regexp='word cloud [\w]+')
@has_url
@print_message_deb
def word_cloud(message):
    """
    Показать облако слов
    """
    list_m = message.text.split()
    color = list_m[-1]
    try:
        dst_photo = currents_chat_url[message.chat.id].word_cloud(color)
        with open(dst_photo, 'rb') as photo:
            bot.send_photo(message.chat.id, photo,
                           reply_markup=telebot.types.ReplyKeyboardRemove())
    except ValueError as e:
        if str(e)[:8] == 'Colormap':
            bot.send_message(message.chat.id, str(e))
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка. '
                                              'Попробуйте позже.')


@bot.message_handler(regexp='describe [\w]+')
@has_url
@print_message_deb
def describe_word(message):
    """
    Показать статистику по слову
    """
    list_m = message.text.split()
    word = list_m[-1]
    d = currents_chat_url[message.chat.id].describe_word(word)
    if len(d) > 0:
        bot.send_message(message.chat.id,
                         '\n'.join('{0}: {1}'.format(p, d[p]) for p in d))
    else:
        bot.send_message(message.chat.id, 'Нет такого слова')


@bot.message_handler(regexp='(describe)')
@has_url
@print_message_deb
def describe(message):
    """
    Показать статистику по текстам
    """
    dest_photo = currents_chat_url[message.chat.id].describe_hist()
    for i in dest_photo:
        with open(i, 'rb') as photo:
            bot.send_photo(message.chat.id, photo,
                           reply_markup=telebot.types.ReplyKeyboardRemove())
    d = currents_chat_url[message.chat.id].describe()
    text = 'count {0}\n'.format(d['frequency']['count'])
    text += '\n'.join(
        p + ': ' +
        ' '.join('{0}={1:.3}'.format(i, d[p][i]) for i in d[p]) for p in d)
    bot.send_message(message.chat.id, text)


@bot.message_handler(content_types=['text'])
@print_message_deb
def no_command(message):
    """
    Реакция на сообщение пользователя без команды
    """
    bot.send_message(message.chat.id, 'Не определена команда. Попробуйте /help'
                                      ' для вывода всех команд.')


if __name__ == '__main__':
    bot.polling()
