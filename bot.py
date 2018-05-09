"""
Скрипт работы телеграм бота
"""
import telebot
import json


with json.load(open('config')) as config:
    bot = telebot.TeleBot(config['token'])

@bot.message_handler(regexp='help')
def show_help(message):
    pass

@bot.message_handler(regexp='write [\d]+')
def write_topN(message):
    list_m = message.split()
    N = int(list_m[1])
    pass

@bot.message_handler(regexp='top [\d]+ (asc|desc)')
def show_topN(message):
    list_m = message.split()
    N = int(list_m[1])
    is_asc = list_m[2].lower_case() == 'asc'
    pass

@bot.message_handler(regexp='stop word')
def stop_word(message):
    pass

@bot.message_handler(regexp='word cloud [\w]+')
def word_cloud(message):
    list_m = message.split()
    color = list_m[-1]
    pass

@bot.message_handler(regexp='describe')
def describe(message):
    pass

@bot.message_handler(regexp='describe [\w]+')
def describe_word(message):
    list_m = message.split()
    word = list_m[-1]
    pass
