from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String
from sqlalchemy.orm import mapped_column
import requests
import os


api_key = os.environ.get("API_KEY")
weather_url = "https://api.openweathermap.org/data/2.5/weather"
geolocation_url = "http://api.openweathermap.org/geo/1.0/direct"
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI", "sqlite:///cities.db")
bootstrap = Bootstrap5(app)
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)


@app.route("/", methods=['GET', 'POST'])
def home():
    cities = db.session.execute(db.Select(City)).scalars()
    weathers = []
    city_name = None
    units = "metric"
    unit = "°C"

    if request.method == "POST":
        city_name = request.form['city-name']
        units = request.form['inlineRadioOptions']
        if units == "metric":
            unit = "°C"
        else:
            unit = "°F"
        location = requests.get(geolocation_url, params={'q': f'{city_name}', 'limit': '1', 'appid': f'{api_key}'}).json()
        lat = location[0]['lat']
        lon = location[0]['lon']
        city_name = location[0]['name']
        r = requests.get(weather_url, params={'lat': f'{lat}', 'lon': f'{lon}', 'units': f'{units}', 'appid': f'{api_key}'}).json()
        weather = {
            'city': city_name,
            'temp': r['main']['temp'],
            'feels_like': r['main']['feels_like'],
            'temp_min': r['main']['temp_min'],
            'temp_max': r['main']['temp_max'],
            'description': r['weather'][0]['description'],
            'icon': r['weather'][0]['icon'],
        }
        weathers.append(weather)

    for city in cities:
        location = requests.get(geolocation_url,
                                params={'q': f'{city.name}', 'limit': '1', 'appid': f'{api_key}'}).json()
        lat = location[0]['lat']
        lon = location[0]['lon']
        city_name = location[0]['name']
        r = requests.get(weather_url, params={'lat': f'{lat}', 'lon': f'{lon}', 'units': f'{units}',
                                                    'appid': f'{api_key}'}).json()
        weather = {
            'city': city.name,
            'temp': r['main']['temp'],
            'feels_like': r['main']['feels_like'],
            'temp_min': r['main']['temp_min'],
            'temp_max': r['main']['temp_max'],
            'description': r['weather'][0]['description'],
            'icon': r['weather'][0]['icon'],
        }

        duplicate = False
        for check in weathers:
            if check['city'] == weather['city']:
                duplicate=True
                break

        if not duplicate:
            weathers.append(weather)

    return render_template("index.html", weathers=weathers, unit=unit)


@app.route("/add", methods=['POST'])
def add_city():
    city_name = request.form['city-name']
    if not db.session.execute(db.select(City).filter_by(name=city_name)).scalar():
        new_city = City(name=city_name)
        db.session.add(new_city)
        db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=9000)
