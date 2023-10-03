import os
from dotenv import load_dotenv
import json
from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, session, flash, abort
from flask_session import Session
import redis
import pymongo
import requests
from bson.objectid import ObjectId


load_dotenv()


MONGO_CLIENT = pymongo.MongoClient(
    f"mongodb+srv://worldhistorytimeline:{os.getenv('MONGODB_PASSWORD')}@cluster0.hemram6.mongodb.net/?retryWrites=true&w=majority&appName=AtlasApp")

DB = MONGO_CLIENT["main"]


app = Flask(__name__)

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(os.getenv('REDIS_URL'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = True
app.config['SESSEION_COOKIE_NAME'] = 'X-Identity'

Session(app)


if MONGO_CLIENT.admin.command('ping')['ok'] == 1:
    print("Connected to MongoDB Atlas")


# @app.after_request
# def add_header(response):
#     response.headers['Cache-Control'] = 'public, max-age= 3600'
#     return response


@app.route('/')
def index():
    century_data = DB.century_data.find().sort("century", pymongo.ASCENDING)
    resposne = make_response(render_template(
        'index.html', century_data=century_data))
    return resposne


@app.route('/<century>')
def century(century):
    if not century.isdigit():
        abort(404)
    decade_data = DB.decade_data.find({"century": century}).sort(
        "decade")
    if decade_data is None:
        decade_data = []
    else:
        decade_data = sorted(decade_data, key=lambda k: int(k['decade']))
    return render_template('century.html', decade_data=decade_data, century=century)


@app.route('/<century>/<decade>')
def decade(century, decade):
    if not century.isdigit() or not decade.isdigit():
        abort(404)
    year_data = DB.year_data.find(
        {"decade": decade, "century": century})

    if year_data is None:
        year_data = []
    else:
        year_data = sorted(year_data, key=lambda k: int(k['year']))

    return render_template('decade.html', year_data=year_data, century=century, decade=decade)


@app.route('/<century>/<decade>/<year>')
def year(century, decade, year):
    if not century.isdigit() or not decade.isdigit() or not year.isdigit():
        abort(404)

    famous_people = DB.famous_people.find(
        {"year": year, "decade": decade, "century": century})
    year_summary = DB.year_data.find_one(
        {"year": str(year), "decade": str(decade), "century": str(century)})

    if famous_people is None:
        famous_people = []

    if year_summary is None:
        year_summary = "No summary is currently available for this year."
    else:
        year_summary = year_summary["summary"]

    return render_template('year.html', famous_people=famous_people, century=century, decade=decade, year=year, year_summary=year_summary)


@app.route('/authentication', methods=['GET', 'POST'])
def authentication():
    '''
    The autentication page is used to log in to the contributor mode of the website.
    '''
    if session.get('logged_in'):
        return redirect(url_for('contribute'))
    return render_template('authentication.html')


@app.route('/github/callback')
def github_callback():
    '''
    The github callback is used to log in to the contributor mode of the website.
    '''
    if session.get('logged_in'):
        return redirect(url_for('contribute'))

    code = request.args.get('code')

    if code is None:
        print("No code provided")
        return redirect(url_for('authentication'))

    try:
        response = requests.post('https://github.com/login/oauth/access_token?client_id={}&client_secret={}&code={}'.format(
            os.getenv('GITHUB_CLIENT_ID'), os.getenv('GITHUB_CLIENT_SECRET'), code), headers={'Accept': 'application/json'}, timeout=5)

        user_data = requests.get('https://api.github.com/user', headers={
            'Authorization': 'Bearer {}'.format(response.json()['access_token'])}, timeout=5).json()

        if user_data['email'] is None:
            email = requests.get('https://api.github.com/user/emails', headers={
                'Authorization': 'Bearer {}'.format(response.json()['access_token'])}, timeout=5).json()
            for record in email:
                if record['primary'] == True:
                    user_data['email'] = record['email']
                    break

        if DB.users.find_one({"email": user_data['email']}) is None:
            DB.users.insert_one({"email": user_data['email'], "contributor": False, "admin": False,
                                "username": user_data['login'], "name": user_data['name'], "avatar_url": user_data['avatar_url']})

        user_info = DB.users.find_one({"email": user_data['email']})

        session['logged_in'] = True
        session['username'] = user_info['username']
        session['name'] = user_info['name']
        session['email'] = user_info['email']
        session['avatar_url'] = user_info['avatar_url']
        session['contributor'] = user_info['contributor']
        session['admin'] = user_info['admin']

        return redirect(url_for('contribute'))
    except Exception as e:
        print(e)
        return redirect(url_for('authentication'))


@app.route('/contribute')
def contribute():
    '''
    The contribute page is used to add new data to the database.
    '''
    if not session.get('logged_in'):
        print("Not logged in")
        return redirect(url_for('authentication'))
    return render_template('contribute.html')


@app.route('/contribute/edit/<data_type>/<id>', methods=['GET', 'POST'])
def edit(data_type, id):
    '''
    The edit page is used to edit existing data in the database.
    '''
    if not session.get('logged_in'):
        return redirect(url_for('authentication'))
    if len(id) != 24:
        abort(404)
    match data_type:
        case "century":
            data = DB.century_data.find_one({"_id": ObjectId(id)})
        case "decade":
            data = DB.decade_data.find_one({"_id": ObjectId(id)})
        case "year":
            data = DB.year_data.find_one({"_id": ObjectId(id)})
        case "famous_people":
            data = DB.famous_people.find_one({"_id": ObjectId(id)})
        case _:
            abort(404)

    print(data)
    if data is None:
        abort(404)
    return "Data: {}".format(data)


if __name__ == '__main__':
    app.run(debug=True)
