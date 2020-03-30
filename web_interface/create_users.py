from flask import Flask
from flask_login import UserMixin
from flask_mongoengine import MongoEngine
from werkzeug.security import generate_password_hash

app = Flask(__name__)

app.config['MONGODB_SETTINGS'] = {
    'host': 'mongodb://localhost:27017/detection_system'
}
db = MongoEngine(app)

class User(UserMixin, db.Document):
  meta = {'collection': 'users'}
  name = db.StringField(max_length=30)
  password = db.StringField()

name = "Sergey.Maltsev"
password = "qwert9876"
hashpass = generate_password_hash(password, method='sha256')
hey = User(name=name,password=hashpass).save()