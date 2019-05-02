from flask import Flask
from flask_session import Session
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.config['SESSION_TYPE'] = 'filesystem'
sess = Session()
sess.init_app(app)

from app import routes
