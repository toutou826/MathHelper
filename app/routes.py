from flask import render_template, flash, redirect, url_for, request
from app.forms import LoginForm, RegistrationForm, UploadForm
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db
from app.models import User, Search
from werkzeug.urls import url_parse
import requests
import sys
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from app.func import get_answer, get_question, allowed_file
import io
from apiclient.http import MediaIoBaseDownload

SCOPES = ['email', 'https://www.googleapis.com/auth/drive.readonly']


#home page where user do the search
@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    form = UploadForm()
    question = None
    if form.validate_on_submit():
        # check if the post request has the file part
        if not form.image.data:
            flash('No file selected.')
            return redirect(url_for('home'))
        file = form.image.data
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for('home'))
        if file and allowed_file(file.filename):
            question = get_question(file)
            return redirect(url_for('search', question = question))
    return render_template('home.html', title='Home', form=form)


@app.route('/uploadDrive', methods=['GET', 'POST'])
def uploadDrive():
    #Get auth token
    flow = InstalledAppFlow.from_client_secrets_file('credential.json', SCOPES)
    creds = flow.run_local_server(port=5200)
    
    #Get drive files and user info
    DRIVE = build('drive', 'v3', credentials=creds)
    client =  build('oauth2', 'v2', credentials=creds)

    info = client.userinfo().get().execute()
    userid, useremail = info.get('id'), info.get('email')

    #If the user is not logged in, check if the user is in userbase
    if current_user.is_anonymous:
        user = User.query.filter_by(email=userid).first()
        #If user has an account, log user in
        if user:
            login_user(user, True)

    if request.method == 'POST':
        fileid = list(request.form.keys())[0]
        req = DRIVE.files().get_media(fileId=fileid)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, req)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        question = get_question(fh.getvalue(), True)
        return redirect(url_for('search', question = question))
    else:
        results = DRIVE.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        items = [i for i in items if '.jpg' in i['name'] or '.png' in i['name']]

    return render_template('uploadDrive.html', title='Upload From Google Drive', items=items)


@app.route('/search', methods=['GET', 'POST'])
def search():
    question = request.args['question']
    answer = get_answer(question)

    if answer:
        body = "\n".join(answer)
        title = answer[0]
        #If user is logged in, save result to recent history
        if not current_user.is_anonymous:
            author = current_user
            searches = Search(title=title, body=body, author=author)
            db.session.add(searches)
            db.session.commit()
        else:
            searches = Search(title=title, body=body)
        return render_template('search.html', title = "Search Result", searches=[searches])
    else:
        flash("Sorry. Cannot get a result for this image.")
        return redirect(url_for('home'))



@app.route('/recent', methods=['GET', 'POST'])
@login_required
def recent():
    searches = current_user.find_search().all()
    return render_template('recent.html', title='Recent Searches', searches=searches)




@app.route('/register', methods=['GET', 'POST'])
def register():
    #If user is logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    #After submitting form, add to database and redirect to login page
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    #If user is logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    #Login user and redirect to the previous page before
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        #Only redirect to relative path
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


