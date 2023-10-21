import os
from dotenv import load_dotenv
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, session, abort
from flask_session import Session
from flask_compress import Compress
from flask_caching import Cache
import redis
import pymongo
import requests
import secrets
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
# cache = Cache(app, config={
#     'CACHE_TYPE': 'simple',
#     'CACHE_DEFAULT_TIMEOUT': 60*60
# })

# def get_cache_key(request):
#     return request.url

# compress = Compress()
# compress.init_app(app)

# compress.cache = cache
# compress.cache_key = get_cache_key

if MONGO_CLIENT.admin.command('ping')['ok'] == 1:
    print("Connected to MongoDB Atlas")


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


@app.after_request
def add_header(response):
    if not request.path.startswith('/static/') and not request.path.startswith('/contribute') and not request.path.startswith('/edit') and not request.path.startswith('/github/callback') and not request.path.startswith('/authentication') and not request.path.startswith('/logout'):
        response.headers['Cache-Control'] = 's-maxage=3600, stale-while-revalidate = 3600', 'public', 'max-age=3600'
    return response


@app.route('/')
def index():
    # session['logged_in'] = True
    # session['username'] = "test"
    # session['name'] = "test"
    # session['email'] = "test"
    # session['avatar_url'] = "test"
    # session['contributor'] = True
    # session['admin'] = True
    # session['userid'] = "test"
    # session['avatar_url'] = "https://avatars.githubusercontent.com/u/96434205"
    century_data = DB.century_data.find().sort("century")
    if century_data is None:
        century_data = []
    else:
        century_data = sorted(century_data, key=lambda k: int(k['century']))
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
        print(decade_data)
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

        if DB.users.find_one({"userid": user_data['id']}) is None:
            DB.users.insert_one({"userid": user_data['id'], "username": user_data['login'], "name": user_data['name'],
                                "email": user_data['email'], "avatar_url": user_data['avatar_url'], "contributor": False, "admin": False})

        user_info = DB.users.find_one({"email": user_data['email']})

        session['logged_in'] = True
        session['userid'] = user_info['userid']
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


@app.route('/account')
def account():
    return redirect(url_for('contribute')), 301


@app.route('/contribute')
def contribute():
    '''
    The contribute page is used to add new data to the database.
    '''
    if not session.get('logged_in'):
        return redirect(url_for('authentication'))
    contributions = []
    for contribution in DB.suggestions.find({"contributor_id": session['userid']}).sort("_id", -1):
        contributions.append(contribution)
    return render_template('contribute.html', contributions=contributions)


@app.route('/contribute/edit/<data_type>/<id>', methods=['GET'])
def edit(data_type, id):
    '''
    The edit page is used to edit existing data in the database.
    '''
    if not session.get('logged_in'):
        return redirect(url_for('authentication'))
    if len(id) != 24:
        abort(404)

    if data_type not in ["century", "decade", "year"]:
        abort(404)

    if data_type == "century":
        data = DB.century_data.find_one({"_id": ObjectId(id)})

        summary = data['summary']
        data_time_period = data['century']
        if data is None:
            abort(404)

    elif data_type == "decade":
        data = DB.decade_data.find_one({"_id": ObjectId(id)})
        summary = data['summary']
        data_time_period = data['decade']

        if data is None:
            abort(404)

    elif data_type == "year":
        data = DB.year_data.find_one({"_id": ObjectId(id)})
        summary = data['summary']
        data_time_period = data['year']
        if data is None:
            abort(404)

    elif data_type == "famous_people":
        data = DB.famous_people.find_one({"_id": ObjectId(id)})
        if data is None:
            abort(404)

    else:
        abort(404)

    return render_template('edit.html', data=data, data_type=data_type, data_time_period=data_time_period, summary=summary, data_id=id)


@app.route('/contribute/edit/famous-people/<id>', methods=['GET'])
def edit_people(id):
    '''
    The edit_people page is used to edit existing data in the database.
    '''
    if not session.get('logged_in'):
        return redirect(url_for('authentication'))
    if len(id) != 24:
        abort(404)

    data = DB.famous_people.find_one({"_id": ObjectId(id)})

    if data is None:
        abort(404)

    return render_template('edit_people.html', data=data, data_id=id)


@app.route('/edit/<data_type>/<id>', methods=['POST'])
def edit_data(data_type, id):
    '''
    The edit_data page is used to edit existing data in the database.
    '''
    if not session.get('logged_in'):
        return redirect(url_for('authentication'))
    if len(id) != 24:
        abort(404)

    data = request.get_json()

    print(data['summary'])

    if data['summary'] == "":
        abort(400)

    if data['sources'] == "":
        abort(400)

    sources = json.loads(data['sources'])
    sources_list = []
    for source in sources:
        sources_list.append(source)

    if data_type == "century":
        original_summary = DB.century_data.find_one(
            {"_id": ObjectId(id)})['summary']
    elif data_type == "decade":
        original_summary = DB.decade_data.find_one(
            {"_id": ObjectId(id)})['summary']
    elif data_type == "year":
        original_summary = DB.year_data.find_one(
            {"_id": ObjectId(id)})['summary']
    else:
        return jsonify({"status": "error", "message": "Invalid form data recived, try again later."})

    DB.suggestions.insert_one({"data_type": data_type, "updated_summary": data['summary'], "updated_sources": sources_list, "data_id": id,
                              "contributor_id": session['userid'], "contributor": session['username'], 'status': 'pending', 'contribution_type': 'edit', 'timestamp': datetime.now().strftime("%d/%m/%Y"), 'original_summary': original_summary})

    return jsonify({"status": "success", 'redirect': '/contribute#contribution-history', 'message': 'Your contribution has been submitted for review.'})


@app.route('/edit/famous-people/<id>', methods=['POST'])
def edit_famous_people_data(id):
    '''
    The edit_data page is used to edit existing data in the database.
    '''
    if not session.get('logged_in'):
        return redirect(url_for('authentication'))
    if len(id) != 24:
        abort(404)

    data = request.get_json()

    if data['summary'] == "":
        abort(400)

    original_summary = DB.famous_people.find_one(
        {"_id": ObjectId(id)})['summary']

    DB.suggestions.insert_one({"data_type": "famous_people", "updated_summary": data['summary'], "data_id": id,
                              "contributor_id": session['userid'], "contributor": session['username'], 'status': 'pending', 'contribution_type': 'edit', 'timestamp': datetime.now().strftime("%d/%m/%Y"), 'original_summary': original_summary})

    return jsonify({"status": "success", 'redirect': '/contribute#contribution-history', 'message': 'Your contribution has been submitted for review.'})


@app.route('/contribute/add/<data_type>', methods=['GET'])
def add(data_type):
    '''
    The add page is used to add new data to the database.
    '''
    if not session.get('logged_in'):
        return redirect(url_for('authentication'))

    if data_type not in ["century", "decade", "year"]:
        century, decade, year = request.args.get(
            'century'), request.args.get('decade'), request.args.get('year')
        if century is None or decade is None or year is None or not century.isdigit() or not decade.isdigit() or not year.isdigit():
            abort(404)
        return render_template('add_famous_people.html', century=century, decade=decade, year=year)
    else:
        if data_type == "century":
            century_value = request.args.get('century')
            if century_value is None or not century_value.isdigit():
                abort(404)
            return render_template('add.html', data_type=data_type, century=century_value)
        elif data_type == "decade":
            century_value = request.args.get('century')
            decade_value = request.args.get('decade')
            if century_value is None or decade_value is None or not century_value.isdigit() or not decade_value.isdigit():
                abort(404)
            return render_template('add.html', data_type=data_type, century=century_value, decade=decade_value)
        elif data_type == "year":
            century_value = request.args.get('century')
            decade_value = request.args.get('decade')
            year_value = request.args.get('year')
            if century_value is None or decade_value is None or year_value is None or not century_value.isdigit() or not decade_value.isdigit() or not year_value.isdigit():
                abort(404)
            return render_template('add.html', data_type=data_type, century=century_value, decade=decade_value, year=year_value)
        else:
            abort(404)


@app.route('/add/summary/<data_type>', methods=['POST'])
def add_summary(data_type):
    '''
    The add_summary page is used to add new data to the database.
    '''
    if not session.get('logged_in'):
        return redirect(url_for('authentication'))

    data = request.get_json()

    if data['summary'] == "":
        abort(400)
    if data['sources'] == "":
        abort(400)

    sources = json.loads(data['sources'])
    sources_list = []
    for source in sources:
        sources_list.append(source)

    if request.args.get('century') is None or (int(request.args.get('century')) >= (int(datetime.now().strftime("%Y")))):
        return jsonify({"status": "error", "message": "Editing a future century is not allowed."})

    if data_type == "century":
        if DB.century_data.find_one({"century": request.args.get('century')}) is not None:
            return jsonify({"status": "error", "message": "Century already exists, please edit the existing century."})
        DB.suggestions.insert_one({"data_type": data_type, "summary": data['summary'], "sources": sources_list, "century": request.args.get(
            'century'), "contributor_id": session['userid'], "contributor": session['username'], 'status': 'pending', 'contribution_type': 'add', 'timestamp': datetime.now().strftime("%d/%m/%Y")})
    elif data_type == "decade":
        if request.args.get('decade') is None:
            return jsonify({"status": "error", "message": "Invalid value for decade provided"})
        if DB.decade_data.find_one({"century": request.args.get('century'), "decade": request.args.get('decade')}) is not None:
            return jsonify({"status": "error", "message": "Decade already exists, please edit the existing decade."})
        DB.suggestions.insert_one({"data_type": data_type, "summary": data['summary'], "sources": sources_list, "century": request.args.get('century'), "decade": request.args.get(
            'decade'), "contributor_id": session['userid'], "contributor": session['username'], 'status': 'pending', 'contribution_type': 'add', 'timestamp': datetime.now().strftime("%d/%m/%Y")})
    elif data_type == "year":
        if request.args.get('decade') is None or request.args.get('year') is None:
            return jsonify({"status": "error", "message": "Invalid value for decade or year provided"})
        if DB.year_data.find_one({"century": request.args.get('century'), "decade": request.args.get('decade'), "year": request.args.get('year')}) is not None:
            return jsonify({"status": "error", "message": "Year already exists, please edit the existing year."})
        DB.suggestions.insert_one({"data_type": data_type, "summary": data['summary'], "sources": sources_list, "century": request.args.get('century'), "decade": request.args.get(
            'decade'), "year": request.args.get('year'), "contributor_id": session['userid'], "contributor": session['username'], 'status': 'pending', 'contribution_type': 'add', 'timestamp': datetime.now().strftime("%d/%m/%Y")})
    else:
        return jsonify({"status": "error", "message": "Invalid data type."})

    return jsonify({"status": "success", 'redirect': '/contribute#contribution-history', 'message': 'Your contribution has been submitted for review.'})


@app.route('/add/summary/famous-people', methods=['POST'])
def add_famous_people_summary():
    '''
    The add_famous_people_summary page is used to add new data to the database.
    '''
    if not session.get('logged_in'):
        return redirect(url_for('authentication'))

    if request.files.get('image') is None or request.form.get('summary') is None or request.form.get('name') is None or request.form.get('lifetime') is None:
        return jsonify({"status": "error", "message": "Invalid data provided."})

    if request.form.get('century') is None or request.form.get('decade') is None or request.form.get('year') is None:
        return jsonify({"status": "error", "message": "Invalid data provided."})

    if len(request.form.get('summary')) > 500:
        return jsonify({"status": "error", "message": "Summary is too long, it should be less than 500 characters."})

    if len(request.form.get('name')) > 20:
        return jsonify({"status": "error", "message": "Name is too long, it should be less than 20 characters."})

    if len(request.form.get('lifetime')) > 20:
        return jsonify({"status": "error", "message": "Lifetime is too long, it should be less than 20 characters."})

    image = request.files.get('image')
    image_id = secrets.token_hex(8)

    response = requests.post("http://ather.api.projectrexa.dedyn.io/upload", files={'file': image.read()}, data={
        'key': f'world-history-timeline/images/{image_id}.{image.filename.split(".")[-1]}', 'content_type': image.content_type, 'public': 'true'}, headers={'X-Authorization': os.getenv('ATHER_API_KEY')}, timeout=10).json()

    if response['status'] == "failed":
        return jsonify({"status": "error", "message": "Failed to upload image, please try again later."})

    image_url = response['access_url']

    DB.suggestions.insert_one({"data_type": "famous_people", "summary": request.form.get('summary'), "name": request.form.get('name'), "lifetime": request.form.get('lifetime'), "image_url": image_url, "century": request.form.get(
        'century'), "decade": request.form.get('decade'), "year": request.form.get('year'), "contributor_id": session['userid'], "contributor": session['username'], 'status': 'pending', 'contribution_type': 'add', 'timestamp': datetime.now().strftime("%d/%m/%Y")})

    return jsonify({"status": "success", 'redirect': '/contribute#contribution-history', 'message': 'Your contribution has been submitted for review.'})


@app.route('/admin/dashboard')
def admin_dashboard():
    '''
    The admin_dashboard page is used to view the admin dashboard.
    '''
    if not session.get('logged_in') or not session.get('admin'):
        abort(404)
    contributions = DB.suggestions.find({'status': 'pending'}) if DB.suggestions.count_documents({
        'status': 'pending'}) > 0 else None
    return render_template('admin_dashboard.html', users=DB.users.find(), number_of_users=DB.users.count_documents({}), number_of_contributions=DB.suggestions.count_documents({}), contributions=contributions)


@app.route('/user/<user_id>')
def user(user_id):
    '''
    The user page is used to view the user dashboard.
    '''
    if not session.get('logged_in'):
        abort(404)

    if user_id.isdigit() == False:
        abort(404)

    user = DB.users.find_one({"userid": int(user_id)})
    print(user)
    if user is None:
        abort(404)
    


    contributions = []
    for contribution in DB.suggestions.find({"contributor_id": int(user_id)}).sort("_id", -1):
        contributions.append(contribution)
    return render_template('profile.html', contributions=contributions, user=user)


@app.route('/logout')
def logout():
    '''
    The logout page is used to log out of the contributor mode of the website.
    '''
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
