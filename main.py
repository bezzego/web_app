import json
import requests
from geopy.distance import geodesic
import folium
from dotenv import load_dotenv
import os


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()

    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        raise ValueError('Адрес не найден.')

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return float(lat), float(lon)  # возвращаем в формате (latitude, longitude)


def load_coffee_data(filepath, encoding='CP1251'):
    with open(filepath, 'r', encoding=encoding) as file:
        return json.load(file)


def calculate_distances_to_user(coffee_data, user_location):
    cafes = []
    for cafe in coffee_data:
        title = cafe['Name']
        latitude = cafe['geoData']['coordinates'][1]
        longitude = cafe['geoData']['coordinates'][0]
        distance = geodesic(user_location, (latitude, longitude)).kilometers

        cafes.append({
            'title': title,
            'latitude': latitude,
            'longitude': longitude,
            'distance': distance
        })
    return cafes


def get_closest_cafes(cafes_with_distances, amount=5):
    return sorted(cafes_with_distances, key=lambda cafe: cafe['distance'])[:amount]


def create_map(user_location, cafes, output_file='index.html'):
    map_object = folium.Map(location=user_location, zoom_start=14)

    folium.Marker(
        location=user_location,
        popup='Вы находитесь здесь',
        icon=folium.Icon(color='red', icon='user')
    ).add_to(map_object)

    for cafe in cafes:
        folium.Marker(
            location=[cafe['latitude'], cafe['longitude']],
            popup=f"{cafe['title']} ({cafe['distance']:.2f} км)",
            icon=folium.Icon(color='green', icon='coffee', prefix='fa')
        ).add_to(map_object)

    map_object.save(output_file)


def main():
    load_dotenv()

    api_key = os.getenv('API_KEY')
    data_file = 'coffee.json'

    address = input('Введите ваш адрес: ')
    try:
        user_location = fetch_coordinates(api_key, address)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return

    coffee_data = load_coffee_data(data_file)
    cafes_with_distances = calculate_distances_to_user(coffee_data, user_location)
    closest_cafes = get_closest_cafes(cafes_with_distances)

    

    create_map(user_location, closest_cafes)

if __name__ == '__main__':
    main()