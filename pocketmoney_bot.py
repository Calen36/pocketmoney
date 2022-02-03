import telebot
from config import TOKEN, DB_FILENAME, ALLOWED_IDS, USERNAMES
from datetime import datetime, timedelta

from dbhandler import DbHandler
from vocabulary import *

'''ALLOWED_IDS = list of telegram id's as integers, i.e. [123456789, 987654321]
USERNAMES = dict of id's and corresponding usernames for use in logging, i.e. {123456789: 'Mom', 987654321: 'Dad'}
'''

bot = telebot.TeleBot(TOKEN, parse_mode='html')
db = DbHandler(DB_FILENAME)


@bot.message_handler(commands=['start', 'старт'])
def send_welcome(message):
    with open('moneycroc.tgs', 'rb') as sticker:
        bot.send_sticker(message.chat.id, sticker)
    if message.chat.id in ALLOWED_IDS:
        keypad = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = telebot.types.KeyboardButton('Баланс')
        item2 = telebot.types.KeyboardButton('Детализация')
        keypad.add(item1, item2)
        bot.reply_to(message, f"Привет, {message.from_user.first_name}! Я - персональный бухгалтер Тимофея.",
                     reply_markup=keypad)
    else:
        bot.reply_to(message, f"Привет, {message.from_user.first_name}! Cожалею, но это бот для частного использования")


@bot.message_handler(commands=['help', 'помощь'])
def helpinfo(message):
    if message.chat.id in ALLOWED_IDS:
        with open('moneycroc.tgs', 'rb') as sticker:
            bot.send_sticker(message.chat.id, sticker)
        bot.reply_to(message, f'Я могу записать приход и расход, для этого напишите что-то вроде "+40 чтение" или "минус 50 мороженное". Могу сообщить баланс или выдать детализацию, для этого напишите, например, "Баланс" или "детализация"')


@bot.message_handler(commands=['reset',])
def reset_dialog(message):
    if message.chat.id in ALLOWED_IDS:
        item1 = telebot.types.InlineKeyboardButton('Отмена', callback_data='cancel')
        item2 = telebot.types.InlineKeyboardButton('УДАЛИТЬ ДАННЫЕ', callback_data='reset_data')
        keypad = telebot.types.InlineKeyboardMarkup([[item1, item2]], row_width=2)
        bot.reply_to(message, f"Это действие безвозвратно удалит все сохраненные данные. Уверены?", reply_markup=keypad)


@bot.message_handler(content_types=['text'])
def process_msg(message):
    if message.chat.id in ALLOWED_IDS and message.chat.type == 'private':
        incoming_text = message.text.strip()
        if any([incoming_text.lower().startswith(x) for x in getbalance_preffixes]):
            reply_message = f"У Тимохи {db.get_total()} рублей"
            print(reply_message)
            bot.send_message(message.chat.id, reply_message)

        elif any([incoming_text.lower().startswith(x) for x in plus_preffixes]):
            incoming_data = parse_msg(incoming_text)
            if incoming_data:
                db.add_money(value=incoming_data['value'], total=db.get_total(), descr=incoming_data['description'][:255], user=USERNAMES[message.chat.id])
                cat = "" if incoming_data['description'] == "Разное" else f" за {incoming_data['description']}"
                reply_message = f"Плюс {incoming_data['value']} рублей{cat}, итого {db.get_total()}"
                print(reply_message)
                bot.send_message(message.chat.id, reply_message)
            else:
                bot.send_message(message.chat.id, f'Не понял вас, повторите')
        elif any([incoming_text.lower().startswith(x) for x in minus_preffixes]):
            incoming_data = parse_msg(incoming_text)
            if incoming_data:
                db.spend_money(value=incoming_data['value'], total=db.get_total(), descr=incoming_data['description'][:255], user=USERNAMES[message.chat.id])
                cat = "" if incoming_data['description'] == "Разное" else f" за {incoming_data['description']}"
                reply_message = f"Минус {incoming_data['value']} рублей{cat}, итого {db.get_total()}"
                print(reply_message)
                bot.send_message(message.chat.id, reply_message)
            else:
                bot.send_message(message.chat.id, f'Не понял вас, повторите')
        elif any([incoming_text.lower().startswith(x) for x in detail_preffixes]):

            item1 = telebot.types.InlineKeyboardButton('Краткая за месяц', callback_data='month_detail_brief')
            item2 = telebot.types.InlineKeyboardButton('Краткая за все время', callback_data='alltime_detail_brief')
            item3 = telebot.types.InlineKeyboardButton('Полная за месяц', callback_data='month_detail_full')
            item4 = telebot.types.InlineKeyboardButton('Полная за все время', callback_data='alltime_detail_full')

            keypad = telebot.types.InlineKeyboardMarkup([[item1, item2], [item3, item4]], row_width=2)
            bot.send_message(message.chat.id, 'За какой период?', reply_markup=keypad)

        else:
            print("сообщение не распознано: ", incoming_text)
            bot.send_message(message.chat.id, f'Не понял вас, повторите')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message.chat.id in ALLOWED_IDS:
        try:
            if call.data == 'month_detail_brief':
                bot.send_message(call.message.chat.id, f"{db.get_summary(limit=datetime.now()-timedelta(days=30), header='30 ДНЕЙ')}")
            elif call.data == 'alltime_detail_brief':
                bot.send_message(call.message.chat.id, f"{db.get_summary(header='ВСЕ ВРЕМЯ')}")
            elif call.data == 'month_detail_full':
                bot.send_message(call.message.chat.id, f"{db.get_detail(limit=datetime.now()-timedelta(days=30), header='30 ДНЕЙ')}")
            elif call.data == 'alltime_detail_full':
                with open('racoon.tgs', 'rb') as sticker:
                    bot.send_sticker(call.message.chat.id, sticker)
                bot.send_message(call.message.chat.id, f"{db.get_detail(header='ВСЕ ВРЕМЯ')}")
            elif call.data == 'cancel':
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            elif call.data == 'reset_data':
                db.reset_db()
                bot.answer_callback_query(callback_query_id=call.id, show_alert=True,
                                          text="Все данные удалены, счет обнулен")
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        except Exception as ex:
            bot.send_message(call.message.chat.id, "ОЙ!")
            print(ex)


bot.polling(none_stop=True)
