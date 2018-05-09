"""
Скрипт работы телеграм бота
"""
import telebot
import json
import re
import os
from word_stat_form_site import WordStatFromSite

with json.load(open('config')) as config:
    bot = telebot.TeleBot(config['token'])

currents_chat_url = {}
# Регулярное выражения для поиска url в тексте
url_reg = r'(?:(?:https?|ftp):\/\/|\b(?:[a-z\d]+\.))(?:(?:[^\s()<>]+|\((?:' \
          r'[^\s()<>]+|(?:\([^\s()<>]+\)))?\))+(?:\((?:[^\s()<>]+|(?:\(?:[^' \
          r'\s()<>]+\)))?\)|[^\s`!()\[\]{};:\'.,<>?«»“”‘’]))?'


def has_url(function):
    def wrapper(message, *args):
        if currents_chat_url.get(message.chat_id, None) is None:
            bot.send_message(message.chat_id, 'Нет текста для анализа')
        else:
            function(message, *args)

    return wrapper


@bot.message_handler(commands=['start'])
def start_bot(message):
    bot.send_message(message.chat_id, 'Привет! Чтобы узнать, как '
                                      'меня использовать, напиши /help.')


@bot.message_handler(regexp=url_reg + r' [\d]+')
def get_url(message):
    url = re.findall(url_reg, message.text)[0]
    depth = int(re.findall(r'[\d]+')[-1])
    currents_chat_url[message.chat_id] = WordStatFromSite(url, depth,
                                                          message.chat_id)
    os.makedirs(os.path.join('.', 'chat_{0}'.format(message.chat_id)))
    bot.send_message(message.chat_id, 'Начинаем анализировать сайты...')
    currents_chat_url[message.chat_id].train_writer()
    currents_chat_url[message.chat_id].gen_stat()
    bot.send_message(message.chat_id, 'Статистика получена.')


@bot.message_handler(commands=['help'])
def show_help(message):
    text = '/start - начать использовать бота\n' \
           '/help - вывести этот текст\n' \
           'write N - написать N слов, используя трёхграммную модель\n' \
           'www.example.com 10 - пример запроса сайта для анализа\n' \
           'top N asc|desc - вывести топ слов по частоте использование.' \
           'N - число слов, asc - в прямом порядке, desc - в обратном\n' \
           'stop word - вывести слова выбросы\n' \
           'word cloud - создать облако слов\n' \
           'describe - статистика по использованию слов\n' \
           'describe WORD - вывести статистику по использованию этого слова\n'
    bot.send_message(message.chat_id, text)


@bot.message_handler(regexp='write [\d]+')
@has_url
def write_N(message):
    list_m = message.split()
    n = int(list_m[1])
    text = currents_chat_url[message.chat_id].write(n)
    bot.send_message(message.chat_id, text)


@bot.message_handler(regexp='top [\d]+ (asc|desc)')
@has_url
def show_topN(message):
    list_m = message.split()
    n = int(list_m[1])
    words = currents_chat_url[message.chat_id].top(n)
    bot.send_message(message.chat_id, '\n'.join(
        ['{0}. {1}'.format(p, w) for p, w in
         zip(range(len(words)), words)]))


@bot.message_handler(regexp='stop word')
@has_url
def stop_word(message):
    words = currents_chat_url[message.chat_id].stop_words()
    bot.send_message(message.chat_id, '\n'.join(
        ['{0}'.format(w) for w in words]))


@bot.message_handler(regexp='word cloud [\w]+')
@has_url
def word_cloud(message):
    list_m = message.split()
    color = list_m[-1]
    dst_photo = currents_chat_url[message.chat_id].word_cloud(color)
    with open(dst_photo, 'rb') as photo:
        bot.send_photo(message.chat_id, photo,
                       reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(regexp='describe')
@has_url
def describe(message):
    d = currents_chat_url[message.chat_id].describe()
    text = 'count {0}\n'.format(d['frequency']['count'])
    text += '\n'.join(
        p + ' '.join('{0}={1}'.format(i, p[i]) for i in p) for p in d)
    bot.send_message(message.chat_id, text)


@bot.message_handler(regexp='describe [\w]+')
@has_url
def describe_word(message):
    list_m = message.split()
    word = list_m[-1]
    d = currents_chat_url[message.chat_id].describe_word(word)
    bot.send_message(message.chat_id,
                     '\n'.join('{0}: {1}'.format(p, d[p]) for p in d))


if __name__ == '__main__':
    bot.polling(none_stop=True)
