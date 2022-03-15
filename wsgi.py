from __init__ import app, socketio, db, csrf
from helper import tasks, helper
from include import filters, views, websocket

from helper.generators import generate_demo

from threading import Thread

from classes.logging import logger
from classes.site_settings import site


def start_threads():

    logger.create_log(logger.LOG_NOTICE, "Server", "Server threads has started")

    #Thread(target=generate_demo, args=(20,), daemon=True).start()
    Thread(target=tasks.clear_rentention, daemon=True).start()
    Thread(target=tasks.create_backup, daemon=True).start()


if __name__ == "__main__":

    logger.create_log(logger.LOG_NOTICE, "Server", "Server has started")

    start_threads()

    app.run(use_reloader=True, debug=True, port=5000)
 