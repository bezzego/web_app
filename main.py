import json
import requests
from geopy.distance import geodesic
from pprint import pprint
import folium
from dotenv import load_dotenv
import os


def fetch_coordinates(address, api_key, api_url):
    params = {
        'apikey': api_key,
        'geocode': f'Москва, {address}',  # добавляем контекст города
        'format': 'json'
    }

    response = requests.get(api_url, params=params)
    response.raise_for_status()

    data = response.json()
    feature_members = data['response']['GeoObjectCollection']['featureMember']

    if not feature_members:
        raise ValueError('Адрес не найден.')

    geo_object = feature_members[0]['GeoObject']
    precision = geo_object['metaDataProperty']['GeocoderMetaData']['precision']

    if precision not in ['exact', 'number', 'near']:  # точные уровни: дом, номер, рядом
        raise ValueError('Адрес найден неточно. Уточните адрес (например: улица, дом).')

    pos = geo_object['Point']['pos']
    longitude, latitude = map(float, pos.split())
    return latitude, longitude


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
    api_url = os.getenv('GEOCODER_API_URL')
    data_file = 'coffee.json'

    address = input('Введите ваш адрес в Москве (например, Арбат, 10): ')
    try:
        user_location = fetch_coordinates(address, api_key, api_url)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return

    coffee_data = load_coffee_data(data_file)
    cafes_with_distances = calculate_distances_to_user(coffee_data, user_location)
    closest_cafes = get_closest_cafes(cafes_with_distances)

    print(f'\nВаши координаты: {user_location}')
    print('\nПять ближайших кофеен:')
    pprint(closest_cafes)

    create_map(user_location, closest_cafes)
    print('\nКарта сохранена в файл index.html')


if __name__ == '__main__':
    main()