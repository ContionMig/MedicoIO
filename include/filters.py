from __init__ import app, db, config

from classes.user import UserData
from datetime import datetime

from flask import render_template, request, session, redirect, flash, url_for, send_file, abort

from classes.site_settings import site

import time, re


@app.template_filter('len')
def filter_len(obj):
    return len(obj)


@app.template_filter('upper')
def filter_upper(text):
    return str(text).upper()


@app.template_filter('u_space')
def filter_spaces(text):
    text = str(text).replace("_", " ")
    return text


@app.template_filter('abr_name')
def filter_abr_name(userid):

    user = UserData(userid=userid)
    abr = user.get_abbreviation() + " " + user.details.get_fname()
    return abr


@app.template_filter('strftime_locale_detail')
def filter_datetime_locale(timestamp):
    converted = time.localtime(int(timestamp))
    return str(time.strftime("%c", converted))


@app.template_filter('strftime_locale')
def filter_datetime_locale(timestamp):
    converted = time.localtime(int(timestamp))
    return str(time.strftime("%d %b %Y", converted))


@app.template_filter('blog_preview')
def filter_blog_preview(content):

    if len(content) <= 200:
        return content

    return str(content)[:200] + "..."


@app.template_filter('blog_title')
def filter_blog_title(content):

    if len(content) <= 40:
        return content

    return str(content)[:40] + "..."


@app.template_filter('htmlclean')
def filter__html_clean(content):
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', str(content))


@app.template_filter('access_control')
def filter__html_clean(url):
    return site.get_access_control_url(url)


@app.template_filter('bk_time')
def filter_bk_time(filename):
    filename = filename[filename.index("_") + len("_"):]
    return str(filename)

@app.template_filter('timec')
def filter_timec(time):
    date_time_obj = datetime.utcfromtimestamp(int(time)).strftime("%Y/%m/%d %H:%M:%S")
    return str(date_time_obj)


@app.template_filter('user_level')
def filter_user_level(userid):
    user = UserData(userid=userid, create=False)

    user_level = []
    for x in user.get_user_level():
        user_level.append(int(x))

    return max(user_level)


@app.template_filter('is_admin')
def filter_is_admin(userid):
    user = UserData(userid=userid, create=False)

    if '0' in user.get_user_level():
        return True

    return False


@app.template_filter('has_access')
def filter_user_level(url):
    user = UserData(userid=session["userid"], create=False)

    if not str(user.get_user_level()) in site.get_access_control_url(url):
        return False

    return True


@app.template_filter('mask')
def filter_mask(text):
    text = str(text)
    mask = text[0]
    
    for x in range(5):
        mask += "*"
    
    mask += text[-4:]

    return mask


@app.template_filter('err_title')
def filter_error_title(err_num):
    err_num = int(err_num)

    if err_num == 0:
        return "LOG_EMERG"
    elif err_num == 1:
        return "LOG_ALERT"
    elif err_num == 2:
        return "LOG_CRIT"
    elif err_num == 3:
        return "LOG_ERR"
    elif err_num == 4:
        return "LOG_WARNING"
    elif err_num == 5:
        return "LOG_NOTICE"
    elif err_num == 6:
        return "LOG_INFO"
    elif err_num == 7:
        return "LOG_DEBUG"
