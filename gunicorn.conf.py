def post_worker_init(worker):
    from wsgi import start_threads, logger
    
    logger.create_log(logger.LOG_NOTICE, "Server", "Server has started")

    start_threads()