from flask import Flask

from flask_socketio import SocketIO
from flask_qrcode import QRcode
from flask_minify import minify
from flask_wtf.csrf import CSRFProtect
from flask_recaptcha import ReCaptcha 
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_bootstrap import Bootstrap

from datetime import datetime, timedelta

from globals import *
from classes import database

from helper.encryption import hashing

import random, time

db = database.database()
app = Flask(__name__)

app.config['SECRET_KEY'] = config["secret_key"]
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=config["session_life"])
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

csrf = CSRFProtect(app)
socketio = SocketIO(app)

minify(app=app, html=True, js=True, cssless=True)
Bootstrap(app)
QRcode(app)

seed = random.Random(int(time.time() / 60 / 60 / 24))
app.secret_key = hashing.urandom_from_random(seed, 1024)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["5 per second"]
)

app.config['RECAPTCHA_SITE_KEY'] = config["reCAPTCHA"]['site_key']
app.config['RECAPTCHA_SECRET_KEY'] = config["reCAPTCHA"]['Secret_key']
recaptcha = ReCaptcha(app)

print("Server Day Seed: ", int(time.time() / 60 / 60 / 24))
print("Server Seed: ", random.Random(int(time.time() / 60 / 60 / 24)))
print("Server Key:", hashing.urandom_from_random(seed, 128))