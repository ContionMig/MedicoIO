from __init__ import app, db, socketio, config

from flask import render_template, request, session, request
from helper import helper

from classes.user import UserData

import time

connected_clients = {}


@socketio.on("connect")
def connect():
   pass


@socketio.on("disconnect")
def disconnect():
    pass