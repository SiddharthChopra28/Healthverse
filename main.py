"""
ToDo:
- API implementation
- Website
- Chrome Extension

"""


from re import template
from flask import Flask, g, render_template, flash, redirect, url_for, abort, request, jsonify #type:ignore
from flask_bcrypt import check_password_hash #type:ignore
from flask_login import LoginManager, login_user, logout_user, login_required, current_user #type:ignore
from flask_cors import CORS #type:ignore
from models import User
import traceback
import os
import math
import uuid
import forms
import models
import json
import datetime
import cv2
import numpy as np

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__, static_folder="static")
app.secret_key = 'asdnafnj#46sjsnvd(*$43sfjkndkjvnskb6441531@#$$6sddf'
app.config.from_object('config.Config')
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.context_processor
def inject_details():
    loggedIn = current_user.is_authenticated
    if not current_user.is_anonymous:
        username = current_user.username
    else:
        username = 'Guest'
    if len(username)>12:
        username = username[:11]+'...'
    return dict(hostname = 'https://'+app.config['SERVER_NAME'], loggedIn=loggedIn, username=username)



@app.before_request
def before_request():
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """close all database connection after each request"""
    g.db.close()
    return response


@app.route("/")
def init():
    print(current_user.is_authenticated)
    if current_user.is_authenticated:
        print(current_user.username)
        return render_template('home.html')

    return render_template('home.html')


@app.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        if form.email.data:
            import requests
            email_address = str(form.email.data)
            response = requests.get(
                "https://isitarealemail.com/api/email/validate",
                params={'email': email_address})

            status = response.json()['status']
            if status == "valid":
                pass
            elif status == "invalid":
                flash("Sorry, No such email exists", "error")
                return render_template('register.html', form=form)
            else:
                flash("Sorry, this email is unknown", "error")
                return render_template('register.html', form=form)
        else:
            flash("Please enter an Email Address", "error")
            return render_template('register.html', form=form)
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            try:
                user = models.User.get(models.User.username == form.username.data)
            except models.DoesNotExist:
                models.User.create_user(
                    username=form.username.data,
                    email=form.email.data,
                    dob = form.dob.data,
                    gender = form.gender.data,
                    password=form.password.data
                )
                
                flash("Registered Successfully", "success")
                return redirect(url_for('login'))
            flash("Sorry, the Username already exists", "error")
        flash("Sorry, the Email is already registered", "error")
    return render_template('register.html', form=form)


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password does not match.", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("You have been logged in", "success")
                return redirect(url_for('init'))
            else:
                flash("Your email or password does not match.", "error")
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('init'))



@app.route("/api", methods=["GET", "POST"])
def api():
    try:
        api_type = request.args.get('type')
        values = [request.args.get('cough'), request.args.get('fever'), request.args.get('sore_throat'), request.args.get('headache'), request.args.get('shortness_of_breath'), request.args.get('contact_with_covid_patient')]
        age = request.args.get('age')
        gender = request.args.get('gender')
    except:
        return "Insufficient values for test"

    global xception_chest, xception_ct

    if api_type == "eval":
        age = int(age)
        try:
            if gender.lower() == "male":
                gender = 0
            elif gender.lower() == "female":
                gender = 1
            else:
                return f"Invalid entry: {gender}. Only enter [male, female]"
            ans = list(map(int, values))
            x = 0.43745532 * ans[0] + 0.86985267 * ans[1] + 0.85234942 * ans[2] + 0.90117341 * ans[3] + 1.2213431 * ans[
                4] + 0.1111888 * int(age) + 0.25830843 * gender + 1.19444185 * ans[5] + 2.54567819
            predict = 1 / (1 + math.e ** (-x))
            if not current_user.is_authenticated:
                return "0x10"
            user_models = json.load(open('beta.json', 'r'))
            if current_user.username not in user_models.keys():
                new_user = user_models
                new_user[current_user.username] = {}
                new_user[current_user.username]["eval"] = {}
                new_user[current_user.username]["xray"] = {}
                new_user[current_user.username]["ct"] = {}
                with open('beta.json', 'w') as files:
                    json.dump(new_user, files)
                user_models = json.load(open('beta.json', 'r'))
            evaluation = user_models
            evaluation[str(current_user.username)]["eval"][str(datetime.datetime.now())] = predict
            with open('beta.json', 'w') as files:
                json.dump(evaluation, files)
            if predict >= 0.5:
                return "Positive"
            elif predict < 0.5:
                return "Negative"
        except Exception:
            we = traceback.print_exc()
            return str(we)

    if request.method == "POST":
        a_type = request.form['type']
        print(request.files)
        print(request.form)
        if "scan_image" not in request.files:
            flash("Please attach a file!")
            if a_type == 'ct':
                return redirect(url_for('ct'))
            elif a_type == 'xray':
                return redirect(url_for('xray'))

        scan_image = request.files['scan_image']
        prefix = scan_image.filename.split(".")[-1]

        if prefix in ALLOWED_EXTENSIONS:
            user_id = uuid.uuid4()
            if a_type == "ct":
                path = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id) + "-ct" + "." + prefix)
                scan_image.save(path)
                filename = path
                
            elif a_type == "xray":
                path = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id) + "-xray" + "." + prefix)
                scan_image.save(path)
                filename = path
                
            else:
                flash("Invalid file extension!")
                return redirect(url_for('ct'))

            if a_type == 'xray':
                covid = 'none'
                
                image = cv2.imread(filename)  # read file
                print(image.size)
                print(path)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # arrange format as per keras
                image = cv2.resize(image, (224, 224))
                image = np.array(image) / 255
                image = np.expand_dims(image, axis=0)
                xception_pred = xception_chest.predict(image)[0][0]
                if not current_user.is_authenticated:
                        flash("User not authenticated!")
                        return redirect(url_for('xray'))
                user_models = json.load(open('beta.json', 'r'))
                if current_user.username not in user_models.keys():
                    new_user = user_models
                    new_user[current_user.username] = {}
                    new_user[current_user.username]["eval"] = {}
                    new_user[current_user.username]["xray"] = {}
                    new_user[current_user.username]["ct"] = {}
                    with open('beta.json', 'w') as files:
                        json.dump(new_user, files)
                    user_models = json.load(open('beta.json', 'r'))
                xray = user_models
                xray[str(current_user.username)]["xray"][str(datetime.datetime.now())] = xception_pred
                with open('beta.json', 'w') as files:
                    json.dump(xray, files)
                if xception_pred > 0.5:
                    covid = "Positive"
                else:
                    covid = "Negative"
                return render_template('xray-scan.html', result=covid)

            elif api_type == "ct":
                covid = 'none'
                image = cv2.imread(os.path.join("static", filename))  # read file
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # arrange format as per keras
                image = cv2.resize(image, (224, 224))
                image = np.array(image) / 255
                image = np.expand_dims(image, axis=0)
                xception_pred = xception_ct.predict(image)[0][0]
                if not current_user.is_authenticated:
                    flash("User not authenticated!")
                    return redirect(url_for('ct'))

                user_models = json.load(open('beta.json', 'r'))
                if current_user.username not in user_models.keys():
                    new_user = user_models
                    new_user[current_user.username] = {}
                    new_user[current_user.username]["eval"] = {}
                    new_user[current_user.username]["xray"] = {}
                    new_user[current_user.username]["ct"] = {}
                    with open('beta.json', 'w') as files:
                        json.dump(new_user, files)
                    user_models = json.load(open('beta.json', 'r'))
                ct = user_models
                ct[str(current_user.username)]["ct"][str(datetime.datetime.now())] = xception_pred
                with open('beta.json', 'w') as files:
                    json.dump(ct, files)
                if xception_pred > 0.5:
                    covid = "Positive"
                else:
                    covid = "Negative"
                return render_template('ct-scan.html', result=covid)


@app.route("/vision")
def about():
  return render_template('vision.html')


@app.route("/api-get")
def get_val_api():
    username = request.args.get('uname')

    user_models = json.load(open('beta.json', 'r'))    
        
    if not username in user_models.keys():
        return "none"
    to_ret = {}
    xray = user_models[username]["xray"]
    ct = user_models[username]["ct"]
    evaluation = user_models[username]["eval"]
    try:
        eval_5 = list(evaluation.keys())[-5:]
    except IndexError:
        eval_5 = list(evaluation.keys())
    try:
        xray_5 = list(xray.keys())[-5:]
    except IndexError:
        xray_5 = list(xray.keys())
    try:
        ct_5 = list(ct.keys())[-5:]
    except IndexError:
        ct_5 = list(ct.keys())
    to_ret[username] = {"eval": {}, "xray": {}, "ct": {}}
    for item in eval_5:
        to_ret[username]["eval"][item] = evaluation[item]
    for item in xray_5:
        to_ret[username]["eval"][xray] = item[item]
    for item in ct_5:
        to_ret[username]["eval"][ct] = ct[item]
    return jsonify(to_ret)


@app.route("/api-auth")
def get_auth_api():
    
    email = request.args.get('email')
    pwd = request.args.get('pwd')
    try:
        user = models.User.get(models.User.email == email)
    except models.DoesNotExist:
        return "False"

    if check_password_hash(user.password, pwd):
        return ','.join([user.username, user.dob, 'Male' if user.gender == '1' else 'Female'])
    return "False"

@app.route("/tests")
@login_required
def test():
    return render_template('tests.html')

@app.route('/self-eval-test')
@login_required
def self_eval_test():
    return render_template('self-eval-test.html', dob=current_user.dob, gender='male' if current_user.gender == '1' else 'female')

@app.route('/ct-scan')
@login_required
def ct():
    return render_template('ct-scan.html')

@app.route('/xray-scan')
@login_required
def xray():
    return render_template('xray-scan.html')


@app.route("/tech")
def tech():
  return render_template('tech-info.html')


@app.errorhandler(500)
def error_500(e):
    return render_template('error_500.html'), 500


@app.errorhandler(404)
def error_404(e):
    return render_template('error_404.html'), 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
