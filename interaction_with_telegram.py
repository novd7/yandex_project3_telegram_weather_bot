import logging
from datetime import datetime

from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler

from API_KEYS import TELEGRAM_TOKEN
from interaction_with_database import *
from interaction_with_YaMaps import *
from interaction_with_YaWeather import *
from getting_text_of_forecast import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


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
    await update.message.reply_text("Я запомнил Ваш город")
    return ConversationHandler.END  # Константа, означающая конец диалога.
    # Все обработчики из states и fallbacks становятся неактивными.

async def weather_for_day(update, context):
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
    

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, locality_response)],
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    
    application.add_handler(conv_handler)
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("weather_for_day", weather_for_day))
    application.add_handler(CommandHandler("weather_for_week", weather_for_week))
    
    # application.add_handler(text_handler)
    
    application.run_polling()


if __name__ == '__main__':
    main()
