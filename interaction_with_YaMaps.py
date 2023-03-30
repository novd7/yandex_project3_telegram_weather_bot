import requests

from API_KEYS import YANDEX_MAPS_API_KEY


def get_coords_by_city_name(city_name: str) -> (float, float):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
    
    geocoder_params = {
        "apikey": YANDEX_MAPS_API_KEY,
        "geocode": city_name,
        "format": "json"}
    
    response = requests.get(geocoder_api_server, params=geocoder_params)
    
    json_response = response.json()
    coords = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
    coords = coords.split()
    lat = float(coords[1])
    lon = float(coords[0])
    return lat, lon


def test_Voronezh():
    allowable_variation = 0.1
    expected_voronezh_centre = (51.660781, 39.200296)
    current_voronezh_centre = get_coords_by_city_name("Воронеж")
    assert expected_voronezh_centre[0] - allowable_variation <= current_voronezh_centre[0] \
           <= expected_voronezh_centre[0] + allowable_variation and \
           expected_voronezh_centre[1] - allowable_variation <= current_voronezh_centre[1] \
           <= expected_voronezh_centre[1] + allowable_variation
