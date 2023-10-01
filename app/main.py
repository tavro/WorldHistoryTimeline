import os
from dotenv import load_dotenv
import json
from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, session, flash, abort
import redis
import pymongo

load_dotenv()


MONGO_CLIENT = pymongo.MongoClient(
    f"mongodb+srv://worldhistorytimeline:{os.getenv('MONGODB_PASSWORD')}@cluster0.hemram6.mongodb.net/?retryWrites=true&w=majority&appName=AtlasApp")

DB = MONGO_CLIENT["main"]


app = Flask(__name__)

if MONGO_CLIENT.admin.command('ping')['ok'] == 1:
    print("Connected to MongoDB Atlas")


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'public, max-age= 3600'
    return response


@app.route('/')
def index():
    century_data = DB.century_data.find()
    resposne = make_response(render_template(
        'index.html', century_data=century_data))
    return resposne


@app.route('/<century>')
def century(century):
    if not century.isdigit():
        abort(404)
    decade_data = DB.decade_data.find({"century": century})
    return render_template('century.html', decade_data=decade_data, century=century)


@app.route('/<century>/<decade>')
def decade(century, decade):
    if not century.isdigit() or not decade.isdigit():
        abort(404)
    year_data = DB.year_data.find({"decade": decade})
    return render_template('decade.html', year_data=year_data, century=century, decade=decade)


@app.route('/<century>/<decade>/<year>')
def year(century, decade, year):
    if not century.isdigit() or not decade.isdigit() or not year.isdigit():
        abort(404)
    famous_people = DB.famous_people.find(
        {"year": year, "decade": decade, "century": century})
    year_summary = DB.year_data.find_one(
        {"year": str(year), "decade": str(decade), "century": str(century)})["summary"]

    return render_template('year.html', famous_people=famous_people, century=century, decade=decade, year=year, year_summary=year_summary)


if __name__ == '__main__':
    app.run(debug=True)
