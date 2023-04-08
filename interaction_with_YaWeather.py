import requests

from API_KEYS import YANDEX_WEATHER_API_KEY


def request_to_Yandex_weather(**kwargs):
    """Sends request to Yandex Weather using kwargs and
    returns json response"""
    
    geocoder_api_server = f"https://api.weather.yandex.ru/v2/forecast?"
    
    for name, value in kwargs.items():
        geocoder_api_server += f"{name}={value}&"
        
    geocoder_api_server = geocoder_api_server[:-1]
    headers = {"X-Yandex-API-Key": YANDEX_WEATHER_API_KEY}
    
    response = requests.get(geocoder_api_server, headers=headers)
    json_response = response.json()
    
    return json_response


def get_weather_for_day(day_number: int, **kwargs):
    """Returns json weather for necessary day using day_number:
    0 - today, 1 - tomorrow, 2 - the day after tomorrow,
    and so on up to 6"""
    
    weather_json = request_to_Yandex_weather(**kwargs)
    weather_of_necessary_day = weather_json['forecasts'][day_number]
    
    result = {
        "date": weather_of_necessary_day['date'],
        "place": weather_json['geo_object']['locality']['name'],
        "weather": {}
    }
    
    for day_part in ("night", "morning", "day", "evening"):
        result['weather'][day_part] = {
            "condition": weather_of_necessary_day['parts'][day_part]['condition'],
            "temperature": weather_of_necessary_day['parts'][day_part]['temp_avg'],
            "wind_dir": weather_of_necessary_day['parts'][day_part]['wind_dir'],
            "wind_speed": weather_of_necessary_day['parts'][day_part]['wind_speed'],
            "pressure": weather_of_necessary_day['parts'][day_part]['pressure_mm'],
            "humidity": weather_of_necessary_day['parts'][day_part]['humidity']
        }
        
    return result


def get_weather_for_week(**kwargs):
    """Returns json weather for a week including the current day"""
    
    weather_json = request_to_Yandex_weather(**kwargs)
    result = {}
    
    for forecast in weather_json['forecasts']:
        result[forecast['date']] = {
            "night": {
                "temperature": forecast['parts']['night_short']['temp'],
                "condition": forecast['parts']['night_short']['condition']
            },
            "day": {
                "temperature": forecast['parts']['day_short']['temp'],
                "condition": forecast['parts']['day_short']['condition']
            }
        }
        
    return result
