from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    searches = db.relationship('Search', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)    

    #Password management with hash
    def set_password(self, password):
            self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    #Finds all searches by user
    def find_search(self):
        return Search.query.filter(Search.user_id==self.id).order_by(Search.timestamp.desc())
    

class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), default="anonymous")

    def __repr__(self):
        return '<Search {}>'.format(self.body)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))