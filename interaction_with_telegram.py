import asyncio
import datetime
import logging

import pytz
from telegram.ext import Application, MessageHandler, \
    filters, CommandHandler, ConversationHandler, \
    CallbackContext
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from API_KEYS import TELEGRAM_TOKEN
from getting_text_of_forecast import *
from interaction_with_YaMaps import *
from interaction_with_YaWeather import *
from interaction_with_database import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
TIME_ZONE = pytz.timezone('Europe/Moscow')
APPLICATION = Application.builder().token(TELEGRAM_TOKEN).build()
CONTEXT = CallbackContext(APPLICATION)


async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    
    with open("WeatherBotPFP.png", 'rb') as img:
        await update.message.reply_photo(
            img
        )
    
    await update.message.reply_text(
        f"Здравствуйте, {update.message.chat.first_name}! Я Бот-Погодник",
        reply_markup=ReplyKeyboardRemove()
    )
    
    await update.message.reply_text(
        f"Пожалуйста, напишите название города, для которого Вы хотите просматривать погоду",
    )
    return 1


async def stop(update, context):
    
    await update.message.reply_text(
        f"Напишите /start, чтобы начать пользоваться ботом",
    )
    
    await update.message.reply_text(
        "Всего доброго!",
        reply_markup=ReplyKeyboardRemove()
    )
    
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
        ['‣ Прогноз на сегодня \N{sun behind cloud}', '‣ Прогноз на завтра \N{sunrise}'],
        ['‣ Прогноз на неделю \N{calendar}', '‣ Настройки \N{gear}'],
        ['‣ Помощь \N{compass}', '‣ Остановить бота \N{cross mark}']
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text(
        "Я запомнил Ваш город...",
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
    
    if message_text == '‣ Прогноз на сегодня \N{sun behind cloud}':
        await weather_for_day(update, context, day_number=0)
        
    elif message_text == '‣ Прогноз на завтра \N{sunrise}':
        await weather_for_day(update, context, day_number=1)
        
    elif message_text == '‣ Прогноз на неделю \N{calendar}':
        await weather_for_week(update, context)
        
    elif message_text == '‣ Настройки \N{gear}':
        reply_keyboard = [
            ['‣ Сменить город \N{cityscape}'],
            ['‣ Выбрать время уведомления \N{alarm clock}'],
            ['‣ Выйти из настроек \N{cross mark}']
        ]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            "Вот и настройки! \n"
            "‣ Посмотрите на клавиатуру Телеграма ⬇️",
            reply_markup=markup
        )

    elif message_text == '‣ Помощь \N{compass}':
        await help_command(update, context)

    elif message_text == '‣ Остановить бота \N{cross mark}':
        await stop(update, context)
        
    elif message_text == '‣ Сменить город \N{cityscape}':
        await update.message.reply_text(
            "Для повторного выбора города перезапустите бота\n"
            "‣ Напишите /start"
        )
        
    elif message_text == '‣ Выйти из настроек \N{cross mark}':
        reply_keyboard = [
            ['‣ Прогноз на сегодня \N{sun behind cloud}', '‣ Прогноз на завтра \N{sunrise}'],
            ['‣ Прогноз на неделю \N{calendar}', '‣ Настройки \N{gear}'],
            ['‣ Помощь \N{compass}', '‣ Остановить бота \N{cross mark}']
        ]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            "Всё настроили! \n"
            "‣ Посмотрите на клавиатуру Телеграма ⬇️",
            reply_markup=markup
        )
        
    elif message_text == '‣ Выбрать время уведомления \N{alarm clock}':
        await daily_forecast_autosend(None, None, datetime.datetime.now(tz=TIME_ZONE), chat_id)
        await update.message.reply_text(
            "Теперь каждый день в это время я буду "
            "присылать Вам погоду\n"
            "• Вот так ⬇️"
        )
        await update.message.reply_text()
        
    else:
        await update.message.reply_text(
            "Извините, но я Вас не понимаю.\n"
            "‣ Напишите /help или нажмите '‣ Помощь \N{compass}' на клавиатуре ниже строки ввода"
        )
        
        
async def help_command(update, context):
    
    await update.message.reply_text(
        "❖ Помощь ❖\n\n"
        "• Обратите внимание на клавиатуру Телеграма — "
        "она расположена ниже строки ввода "
        "текста в приложении и слева от значка «скрепка» "
        "на сайте\n"
        "• На клавиатуре Вы увидите все нужные функции:\n\n"
        "  ‣ Прогноз на день \N{sun behind cloud} — выводит прогноз погоды на "
        "текущую дату (ночь, утро, день и вечер): "
        "погоду, температуру в °C, направление и скорость ветра, влажность и атмосферное давление\n"
        "  ‣ Прогноз на завтра \N{sunrise} — выводит прогноз погоды на завтра, считая от "
        "текущей даты (ночь, утро, день и вечер): "
        "погоду, температуру в °C, направление и скорость ветра, влажность и атмосферное давление\n"
        "  ‣ Прогноз на неделю \N{calendar} — выводит прогноз погоды на неделю, считая от "
        "текущей даты включительно (7 дат, для каждой — ночь и день): "
        "погоду и температуру в °C\n"
        "  ‣ Помощь \N{compass} — выводит справку со всеми доступными командами\n"
        "  ‣ Остановить бота \N{cross mark} — выход из диалога с ботом\n"
        "  ‣ Настройки \N{gear} — выводит дополнительную клавиатуру со следующими функциями:\n\n"
        "        ‣ Сменить город \N{cityscape} — предлагает перезапустить бота "
        "с помощью команды /start для повторного "
        "выбора города\n"
        "        ‣ Выбрать время уведомления \N{alarm clock} — выставляет текущее время для ежедневной "
        "отправки прогноза на день\n"
        "        ‣ Выйти из настроек \N{cross mark} — возвращает основную клавиатуру\n"

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
    
    restart_schedules()
    APPLICATION.run_polling()


if __name__ == '__main__':
    main()
