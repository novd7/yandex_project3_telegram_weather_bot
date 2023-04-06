import asyncio
import datetime
import logging

import pytz
from telegram.ext import Application, MessageHandler, \
    filters, CommandHandler, ConversationHandler, \
    CallbackContext
from telegram import ReplyKeyboardMarkup

from API_KEYS import TELEGRAM_TOKEN
from getting_text_of_forecast import *
from interaction_with_YaMaps import *
from interaction_with_YaWeather import *
from interaction_with_database import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
TIME_ZONE = pytz.timezone('Europe/Moscow')
APPLICATION = Application.builder().token(TELEGRAM_TOKEN).build()
CONTEXT = CallbackContext(APPLICATION)


async def start(update, context):
    print(update)
    """Отправляет сообщение когда получена команда /start"""
    await update.message.reply_text(
        f"Здравствуйте, {update.message.chat.first_name}! Я бот-погодник.",
    )
    await update.message.reply_text(
        f"Пожалуйста, напишите город, для которого хотите просматривать погоду.",
    )
    return 1


async def stop(update, context):
    await update.message.reply_text(
        f"Напишите /start, чтобы начать пользоваться ботом.",
    )
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


async def locality_response(update, context):
    # Ответ на второй вопрос.
    # Мы можем его сохранить в базе данных или переслать куда-либо.
    locality = update.message.text
    logger.info(locality)
    print(locality)
    coords = get_coords_by_city_name(locality)
    user_id = update.message.from_user.id
    insert_lat_lon_in_database(user_id, *coords)
    reply_keyboard = [
        ['Прогноз на сегодня', 'Прогноз на завтра'],
        ['Прогноз на неделю'],
        ['Настройки']
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text(
        "Я запомнил Ваш город",
        reply_markup=markup
    )
    return ConversationHandler.END  # Константа, означающая конец диалога.
    # Все обработчики из states и fallbacks становятся неактивными.


async def weather_for_day(update, context, day_number=None):
    if day_number is None:
        day_number = int(update.message.text.split()[1])
    user_id = update.message.from_user.id
    coordinates = get_lat_lon_by_user_id(user_id)
    params = {'lat': coordinates[0], 'lon': coordinates[1]}
    data = get_weather_for_day(day_number, **params)
    message = get_message_text_for_day_forecast(data)
    await update.message.reply_html(message)


async def weather_for_week(update, context):
    user_id = update.message.from_user.id
    coordinates = get_lat_lon_by_user_id(user_id)
    params = {'lat': coordinates[0], 'lon': coordinates[1]}
    data = get_weather_for_week(**params)
    message = get_message_text_for_week_forecast(data)
    await update.message.reply_html(message)


def func_of_daily_forecast_autosend(chat_id, day_number=0):
    api_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    coordinates = get_lat_lon_by_user_id(chat_id)
    params = {'lat': coordinates[0], 'lon': coordinates[1]}
    data = get_weather_for_day(day_number, **params)
    message = get_message_text_for_day_forecast(data)
    requests.post(api_url, json={'chat_id': chat_id, 'text': message, "parse_mode": "html"})


async def daily_forecast_autosend(update, context, time: datetime.time, chat_id=None):
    print(chat_id, "-", time)
    hour = time.hour
    minute = time.minute
    second = time.second + 1
    if chat_id is None:
        chat_id = update.message.chat_id
    insert_notification_time(chat_id, hour, minute)
    CONTEXT.job_queue.run_daily(
        lambda *args: func_of_daily_forecast_autosend(chat_id),
        datetime.time(
            hour=hour,
            minute=minute,
            second=second,
            tzinfo=TIME_ZONE
        ),
        chat_id=chat_id
    )


def restart_schedules():
    data = get_schedules()
    for chat_id, hour, minute in data:
        print(chat_id, hour, minute)
        CONTEXT.job_queue.run_daily(
            lambda *args: func_of_daily_forecast_autosend(chat_id),
            datetime.time(
                hour=hour,
                minute=minute,
                second=0,
                tzinfo=TIME_ZONE
            ),
            chat_id=chat_id
        )
        print(chat_id, hour, minute)
    print("Done")
    
    
async def text_listener(update, context):
    message_text = update.message.text
    chat_id = update.message.chat_id
    if message_text == "Прогноз на сегодня":
        await weather_for_day(update, context, day_number=0)
    elif message_text == "Прогноз на завтра":
        await weather_for_day(update, context, day_number=1)
    elif message_text == "Прогноз на неделю":
        await weather_for_week(update, context)
    elif message_text == "Настройки":
        reply_keyboard = [
            ['Сменить город'],
            ['Сменить время уведомления'],
            ['Выйти из настроек']
        ]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            "Вот и настройки ⬇️\n"
            "Посмотрите на клавиатуру Телеграмма",
            reply_markup=markup
        )
    elif message_text == "Сменить город":
        await update.message.reply_text(
            "Давайте начнём всё с начала! Напишите /start"
        )
    elif message_text == "Выйти из настроек":
        reply_keyboard = [
            ['Прогноз на сегодня', 'Прогноз на завтра'],
            ['Прогноз на неделю'],
            ['Настройки']
        ]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            "Всё настроили\n"
            "Посмотрите на клавиатуру Телеграмма",
            reply_markup=markup
        )
    elif message_text == "Сменить время уведомления":
        await daily_forecast_autosend(None, None, datetime.datetime.now(tz=TIME_ZONE), chat_id)
        await update.message.reply_text(
            "Теперь каждый день в это время я буду "
            "присылать Вам погоду. Вот так ⬇️"
        )
    else:
        await update.message.reply_text(
            "Извините, но я Вас не понимаю."
            "Напишите /help"
        )
        
        
async def help_command(update, context):
    await update.message.reply_text(
        "Помощь:\n"
        "Обратите внимание на клавиатуру Телеграмма."
        "На ней Вы увидите все нужные функции.\n"
        "Клавиатура расположена ниже строки ввода "
        "текста в приложении и слева от значка «Скрепка»"
        "в на сайте."
    )


def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, locality_response)],
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    APPLICATION.add_handler(conv_handler)
    
    APPLICATION.add_handler(CommandHandler("start", start))
    APPLICATION.add_handler(CommandHandler("stop", stop))
    APPLICATION.add_handler(CommandHandler("help", help_command))
    APPLICATION.add_handler(CommandHandler("weather_for_day", weather_for_day))
    APPLICATION.add_handler(CommandHandler("weather_for_week", weather_for_week))
    APPLICATION.add_handler(CommandHandler("notifications_for_day",
                                           lambda *args: daily_forecast_autosend(*args,
                                                                                 datetime.datetime.now(tz=TIME_ZONE))))
    APPLICATION.add_handler(MessageHandler(filters.TEXT, text_listener))
    
    # queue = asyncio.Queue
    # updater = Updater(TELEGRAM_TOKEN, queue)
    # j = updater.job_queue
    # job_daily = j.run_daily(daily_job, days=(0, 1, 2, 3, 4, 5, 6),
    #                         time=datetime.time(hour=10, minute=00, second=00))
    
    # application.add_handler(text_handler)
    
    restart_schedules()
    APPLICATION.run_polling()


if __name__ == '__main__':
    main()
