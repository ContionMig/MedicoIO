from __init__ import app, db, socketio, config

import requests, time
from include import websocket

from classes.user import UserData
from classes.user_details import UserDetailData
from classes.images import ImagesData
from classes.consultations import ConsultationData

from classes.site_settings import site

from classes.logging import logger

def clear_rentention():

    time.sleep(10)

    while True:
        
        now = int(time.time())

        db.Execute(f"DELETE FROM {UserData.table} WHERE login_date < ?", (int(now - int(site.get_user_rention()) * 30 * 24 * 60 * 60), ))
        db.Execute(f"DELETE FROM {UserDetailData.table} WHERE login_date < ?", (int(now - int(site.get_user_rention()) * 30 * 24 * 60 * 60), ))

        db.Execute(f"DELETE FROM {ImagesData.table} WHERE timestamp < ?", (int(now - int(site.get_image_rention()) * 30 * 24 * 60 * 60), ))

        db.Execute(f"DELETE FROM {ConsultationData.table} WHERE timestamp < ?", (int(now - int(site.get_consultation_rention()) * 30 * 24 * 60 * 60), ))

        db.Commit()
        time.sleep(3000)



def create_backup():

    time.sleep(10)

    while True:

        time.sleep(86400)

        db.Backup()

