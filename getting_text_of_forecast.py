def get_weather_condition_symbol(condition: str, day_time: str) -> str:
    symbols = {
        "clear": {
            "day": "☀️",
            "night": "🌙"
        },
        "partly-cloudy": "🌤️",
        "cloudy": "🌤️",
        "overcast": "☁️",
        "drizzle": "🌦️",
        "light-rain": "🌦️",
        "rain": "🌦️",
        "moderate-rain": "🌧️",
        "heavy-rain": "🌧️",
        "continuous-heavy-rain": "🌧️",
        "showers": "🌧️",
        "wet-snow": "🌨️",
        "light-snow": "🌨️",
        "snow": "🌨️",
        "snow-showers": "🌨️",
        "hail": "🌧️",
        "thunderstorm": "🌩️",
        "thunderstorm-with-rain": "⛈️",
        "thunderstorm-with-hail": "⛈️"
    }
    
    if condition not in symbols.keys():
        return ""
    
    if isinstance(symbols[condition], dict):
        return symbols[condition][day_time]
    
    return symbols[condition]


def translate_condition(condition: str) -> str:
    dictionary = {
        "clear": "ясно",
        "partly-cloudy": "малооблачно",
        "cloudy": "облачно с прояснениями",
        "overcast": "пасмурно",
        "drizzle": 'морось',
        "light-rain": "небольшой дождь",
        "rain": "дождь",
        "moderate-rain": "умеренно сильный дождь",
        "heavy-rain": "сильный дождь",
        "continuous-heavy-rain": "длительный сильный дождь",
        "showers": "ливень",
        "wet-snow": "дождь со снегом",
        "light-snow": "небольшой снег",
        "snow": "снег",
        "snow-showers": "снегопад",
        "hail": "град",
        "thunderstorm": "гроза",
        "thunderstorm-with-rain": "дождь с грозой",
        "thunderstorm-with-hail": "гроза с градом"
    }
    
    print(condition, dictionary[condition.replace(" ", "")], sep='\n')
    return dictionary[condition.replace(" ", "")]


def translate_wind_dir(wind_dir: str) -> str:
    
    wind_dir = wind_dir.replace("N", "С")
    wind_dir = wind_dir.replace("S", "Ю")
    wind_dir = wind_dir.replace("W", "З")
    wind_dir = wind_dir.replace("E", "В")
    
    return wind_dir


def get_message_text_for_day_forecast(data: dict):
    
    message = f"<b>❖ Погода на {data['date']} в городе {data['place']} ❖</b>\n\n"
    for rus, eng, for_symbol in zip(("<b>•<u> Ночью</u></b> (0 - 5 часов)",
                                     "<b>•<u> Утром</u></b> (6 - 11 часов)",
                                     "<b>•<u> Днём</u></b> (12 - 17 часов)",
                                     "<b>•<u> Вечером</u></b> (18 - 23 часов)"),
                                    ("night", "morning", "day", "evening"),
                                    ("night", "day", "day", "night")):
    
        message += f"{rus}:\n" \
                   f"   {get_weather_condition_symbol(data['weather'][eng]['condition'], for_symbol)} " \
                   f"{translate_condition(data['weather'][eng]['condition'])} " \
                   f"<u><b>{data['weather'][eng]['temperature']}°C</b></u>\n"
        message += f"  ‣ Ветер: {translate_wind_dir(data['weather'][eng]['wind_dir'].upper())}, " \
                   f"{data['weather'][eng]['wind_speed']} м/с\n"
        message += f"  ‣ Влажность: {data['weather'][eng]['humidity']}%\n"
        message += f"  ‣ Давление: {data['weather'][eng]['pressure']} мм рт. ст.\n\n"
    
    return message


def get_message_text_for_week_forecast(data: dict):
    message = f"<b>❖ Прогноз на ближайшие 7 дней ❖</b>\n\n"
    
    for date in data.keys():
        message += f"<b><u>{date}</u></b>\n"
        message += f"  • Ночью (0 - 5 часов): \n" \
                   f"        {get_weather_condition_symbol(data[date]['night']['condition'], 'night')} " \
                   f"{translate_condition(data[date]['night']['condition'])}, " \
                   f"{data[date]['night']['temperature']}°C\n"
        message += f"  • Днём (6 - 23 часов): \n" \
                   f"        {get_weather_condition_symbol(data[date]['day']['condition'], 'day')} " \
                   f"{translate_condition(data[date]['day']['condition'])}, " \
                   f"{data[date]['day']['temperature']}°C\n\n"
    
    return message
