from argparse import Action
from ipaddress import ip_address

import time, os, io, platform, psutil, socket, user_agents, pyotp
from charset_normalizer import logging
from __init__ import app, db, config, limiter, recaptcha

from flask import render_template, request, session, redirect, flash, url_for, send_file, abort

from classes.ip_blacklist import IPBlacklistData, ip_manager
from classes.user import UserData, user_manager
from classes.logging import LoggingData, logger
from classes.site_settings import SiteSettingsData, site

from base64 import b64encode

from helper import helper, encryption


#######################
#   UNIVERSAL FUNC    #
#######################
def access_control(func_name):

    if request.headers.getlist("X-Forwarded-For"):
        ip_address = request.headers.getlist("X-Forwarded-For")[0]
        ip_address = ip_address.split(",")
        ip_address = ip_address[0]
    else:
        ip_address = str(request.remote_addr)
    
    if 'userid' not in session:
        session.clear()
        flash("You are not logged on")
        return redirect(url_for("index"))

    if ip_manager.is_blocked(ip_address):
        flash('You have been blocked for 1 hour due to too many violations!')
        session.clear()
        return redirect(url_for("index"))

    if user_agents.parse(str(request.user_agent)).is_bot:
        logger.create_log(logger.LOG_WARNING, "Authentication", f"[{ip_address}] {request.url} - Crawler detected, rejecting request")
        
        return abort(403, 'You do not have permission to enter this page')  

    user = UserData(userid=session['userid'])

    if not user.is_valid():

        session.clear()
        flash("You are logged in as an invalid user")
        logger.create_log(logger.LOG_WARNING, "Authentication", f"[{ip_address}] {request.url} - Invalid user {user.details.get_nric()} detected, rejected request")
        return redirect(url_for("index"))


    if not user.get_user_level() in site.get_access_control_url(func_name):
        ip_manager.add_violation(ip_address)
        logger.create_log(logger.LOG_WARNING, "Authentication", f"[{ip_address}] {request.url} - User {user.details.get_nric()} tried to access page not authroized, rejecting request")
        return abort(403, 'You do not have permission to enter this page') 


    if 'session_lock' in session:
        if  f"{ip_address}_{str(request.user_agent)}" != session['session_lock']:
            
            ip_manager.add_violation(ip_address)
            logger.create_log(logger.LOG_WARNING, "Authentication", f"[{ip_address}] {request.url} - Invalid session lock user {user.details.get_nric()} detected, rejected request")
            flash("Your session does not match the logged on session!")
            
            session.clear()
            return redirect(url_for("logout"))

    return user

#######################
#  UNIVERSAL ROUTES   #
#######################
@app.after_request
def after_request(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


@app.route("/pfp/<uid>")
@limiter.exempt
def show(uid):

    user = access_control(show.__name__)
    if type(user) != UserData:
        return "error"

    if not uid == "x":
        user = UserData(userid=uid)

    return send_file(
        io.BytesIO(user.get_pfp()),
        mimetype='image/jpeg',
        as_attachment=False,
        attachment_filename='user_profile_picture.jpg')



@app.route("/image/<imacon>")
@limiter.exempt
def show_image(imacon):

    user = access_control(show_image.__name__)
    if type(user) != UserData:
        return "error"

    return send_file(
        io.BytesIO(user.images.retrive_image(imacon)),
        mimetype='image/jpeg',
        as_attachment=False,
        attachment_filename='images.jpg')


@app.route("/blog/image/<blogid>")
@limiter.exempt
def show_blog_image(blogid):

    user = access_control(show_blog_image.__name__)
    if type(user) != UserData:
        return "error"

    return send_file(
        io.BytesIO(user.blogs.retrive_blog(blogid).get_image()),
        mimetype='image/jpeg',
        as_attachment=False,
        attachment_filename='images.jpg')


#######################
#   LOGIN/REGISTER    #
#######################
@app.route('/', methods=['GET', 'POST'])
@limiter.limit("50 per minute")
def index():
    
    logger.create_view(request)

    if 'userid' in session:
        return redirect(url_for("panel"))

    if request.method == 'POST':
        
        if not recaptcha.verify():
            flash("Please fill out the ReCaptcha!")
            return redirect(url_for("index"))

        if request.headers.getlist("X-Forwarded-For"):
            ip_address = request.headers.getlist("X-Forwarded-For")[0]
            ip_address = ip_address.split(",")
            ip_address = ip_address[0]
        else:
            ip_address = str(request.remote_addr)
    
        if ip_manager.is_blocked(ip_address):
            session.clear()
            flash('You have been blocked for 1 hour due to too many violations!')
            return redirect(url_for("index"))
        
        nric = str(request.form['nric']).strip().lower()
        password = str(request.form['password'])

        user = UserData(nric)
        if not user.exist() or not user.is_valid():
            
            ip_manager.add_violation(ip_address)
            
            flash("User credentials are wrong!")
            return redirect(url_for("index"))
        
        
        if not user.verify_password(password):
            
            ip_manager.add_violation(ip_address)
            
            flash("User credentials are wrong!")
            return redirect(url_for("index"))


        session.clear()
        if user.get_otp() == "0":
       
            session['userid'] = user.id()
            session['session_lock'] = f"{ip_address}_{str(request.user_agent)}"
            session.permanent = False

            user.set_ip_address(ip_address)
            user.set_login_date()

            logger.create_log(logger.LOG_NOTICE, "Authentication", f"User {user.details.get_nric()} has logged in")

            flash("Welcome User!")
            return redirect(url_for("panel"))
        
        else:

            session['temp'] = user.id()
            session['session_lock'] = f"{ip_address}_{str(request.user_agent)}"
            session.permanent = False

            logger.create_log(logger.LOG_NOTICE, "Authentication", f"User {user.details.get_nric()} has triggered 2FA")

            return redirect(url_for('index_2fa') )

    
    else:
        return render_template("authentication/index.html")


@app.route('/login/2fa', methods=['GET', 'POST'])
@limiter.limit("50 per minute")
def index_2fa():
    
    logger.create_view(request)

    if 'temp' not in session:
        flash("Please try to log in")
        return redirect(url_for("index"))

    if request.method == 'POST':

        otp = str(request.form['otp'])
        user = UserData(userid=session['temp'])

        if not user.is_valid():
            session.clear()
            flash("You are logged in as an invalid user")
            return redirect(url_for("index"))

        totp = pyotp.TOTP(user.get_otp())

        if not otp == str(totp.now()):
            session.clear()
            flash("The 6 digit code was invalid, please try again!")
            return redirect(url_for('index'))

        if request.headers.getlist("X-Forwarded-For"):
            ip_address = request.headers.getlist("X-Forwarded-For")[0]
            ip_address = ip_address.split(",")
            ip_address = ip_address[0]
        else:
            ip_address = str(request.remote_addr)
    
        session.clear()
        session['userid'] = user.id()
        session['session_lock'] = f"{ip_address}_{str(request.user_agent)}"
        session.permanent = False

        user.set_ip_address(ip_address)
        user.set_login_date()

        logger.create_log(logger.LOG_NOTICE, "Authentication", f"User {user.details.get_nric()} has logged in")

        flash("Welcome User!")
        return redirect(url_for("panel"))
    

    return render_template("authentication/2fa.html")


@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("1 per second")
def register():
    
    logger.create_view(request)

    if request.method == 'GET':

        nric = str(request.args['nric']).strip().lower()
        password = str(request.args['password'])
        user_level = str(request.args['user_level'])

        if not helper.verify_nric(nric):
            flash("Please enter a valid NRIC!")
            return redirect(url_for("index"))

        user = UserData(nric, create=True)
        user.set_password(password)
        user.set_user_level(user_level)
        user.details.set_nric(nric)

        db.Commit()

        logger.create_log(logger.LOG_NOTICE, "Authentication", f"User {user.details.get_nric()} has registered")

        user = UserData(nric, create=False)
        if not user.exist() or not user.is_valid():
            flash("Faield at creating a new user!")
            return redirect(url_for("index"))

        flash("Created new user!")

    return redirect(url_for("index"))


@app.route('/logout')
def logout():
    
    logger.create_view(request)

    if 'userid' in session:
        user = UserData(userid=session['userid'])
        if type(user) != UserData:
            return user

        logger.create_log(logger.LOG_NOTICE, "Authentication", f"User {user.details.get_nric()} has logged out")
        session.clear()

        flash("You have logged out!")

    return redirect(url_for("index"))



#######################
#    PANEL/USERS      #
#######################
@app.route('/panel', methods=['GET'])
def panel():

    logger.create_view(request)

    user = access_control(panel.__name__)
    if type(user) != UserData:
        return user

    return render_template("panel/main.html")


@app.route('/panel/view/consultations', methods=['GET'])
def view_consultations():
    
    logger.create_view(request)

    user = access_control(view_consultations.__name__)
    if type(user) != UserData:
        return user

    return render_template("panel/view_consultations.html", sys=user.consultation, consultation=user.consultation.retrieve_consultation())


@app.route('/panel/view/images', methods=['GET'])
def view_images():
    
    logger.create_view(request)

    user = access_control(view_images.__name__)
    if type(user) != UserData:
        return user

    images = user.images.retrive_images()
    search = request.args.get("search")
    
    if search:
        images = user.images.retrive_images(search)

    return render_template("panel/view_images.html", sys=user.images, images=images)


@app.route('/view/blogs/<blogid>', methods=['GET'])
def view_post(blogid):
    
    logger.create_view(request)

    user = access_control(view_post.__name__)
    if type(user) != UserData:
        return user

    blog = user.blogs.retrive_blog(blogid)
    if not blog.exist():
        flash("Blog post does not exist!")
        return redirect(url_for("panel"))

    return render_template("panel/posts.html", blog=blog)


@app.route('/panel/view/blogs', methods=['GET'])
def view_blogs():
    
    logger.create_view(request)

    user = access_control(view_blogs.__name__)
    if type(user) != UserData:
        return user

    blogs = user.blogs.retrive_blogs(limit=24)
    return render_template("panel/blogs.html", blogs=blogs)


@app.route('/panel/details', methods=['GET', 'POST'])
def panel_details():

    logger.create_view(request)

    user = access_control(panel_details.__name__)
    if type(user) != UserData:
        return user

    if request.method == 'POST':

        if not recaptcha.verify():
            flash("Please fill out the ReCaptcha!")
            return redirect(url_for("index"))

        ic_num = helper.remove_symbol(request.form['nric'])

        f_name = helper.remove_symbol(request.form['f_name'])
        l_name = helper.remove_symbol(request.form['l_name'])

        addr = str(request.form['addr'])

        email = str(request.form['email'])
        contact = helper.remove_symbol(request.form['contact'])
        dob = str(request.form['dob'])

        postal = str(request.form['postal'])
        area = str(request.form['area'])
        
        if 'pfp' in request.files:
            file = request.files['pfp']

            if file.filename != '' and file:
                if helper.allowed_file(file.filename):
                    user.set_pfp(file.read())
                else:
                    flash("The extention of the image you uploaded is no allowed!")


        user.details.set_fname(f_name)
        user.details.set_lname(l_name)
        user.details.set_addr(addr)
        user.details.set_email(email)
        user.details.set_contact(contact)
        user.details.set_dob(dob)
        user.details.set_postal_code(postal)
        user.details.set_area(area)

        flash("Your details has been updated!")
        return redirect(url_for("panel_details"))

    nric_empty = True
    if helper.verify_nric(user.details.get_nric()):
        nric_empty = False

    return render_template("panel/details.html", user=user, nric_empty=nric_empty)


@app.route('/panel/medical/document', methods=['GET'])
def panel_medical():

    logger.create_view(request)
    
    user = access_control(panel_medical.__name__)
    if type(user) != UserData:
        return user

    return render_template("panel/view_medical.html", user=user)


@app.route('/panel/security', methods=['GET', 'POST'])
def panel_security():

    logger.create_view(request)
    
    user = access_control(panel_security.__name__)
    if type(user) != UserData:
        return user

    if request.method == 'POST':

        action = str(request.form['action'])

        if action == "basic_security":
        
            old_pass = str(request.form['old_pass'])
            new_pass = str(request.form['new_pass'])
            new_pass_again = str(request.form['new_pass_again'])

            if new_pass != new_pass_again:
                flash("New passwords does not match!")
                return redirect(url_for('panel_security'))

            verify_pass = helper.password_check(new_pass)
            if not verify_pass[0]:
                flash(verify_pass[1])
                return redirect(url_for("panel_security"))

            if not user.verify_password(old_pass):
                flash("Your current password is wrong!")
                return redirect(url_for("panel_security"))

            user.set_password(new_pass)
            flash("You have successfully changed your password!")

        elif action == "2fa":

            if user.get_otp() == "0":
                otp_code = request.form['otp_code']
                otp = str(request.form['otp'])

                totp = pyotp.TOTP(otp_code)
                if not otp == str(totp.now()):
                    flash("The 6 digit code was invalid, please rescan and try again!")
                    return redirect(url_for('panel_security'))
                
                user.set_otp(otp_code)

                flash("2 Factor Authenticaion has been added!")
                return redirect(url_for('panel_security'))

            else:
                otp = str(request.form['otp'])
                totp = pyotp.TOTP(user.get_otp())

                if not otp == str(totp.now()):
                    flash("The 6 digit code was invalid, please try again!")
                    return redirect(url_for('panel_security'))

                user.set_otp(0)

                flash("2 Factor Authenticaion has been disabled!")
                return redirect(url_for('panel_security'))

    if user.get_otp() == "0":
        two_fa = pyotp.random_base32()
        return render_template("panel/security.html", user=user, otp=two_fa, factor_url=pyotp.totp.TOTP(two_fa).provisioning_uri(name=user.details.get_email(), issuer_name='MedicoIO'))
    else:
        return render_template("panel/security.html", user=user, otp=None)


#######################
#    PANEL/DOCTOR     #
#######################
@app.route('/panel/doctor/patients/add', methods=['GET', 'POST'])
def doc_patient():

    logger.create_view(request)

    user = access_control(doc_patient.__name__)
    if type(user) != UserData:
        return user


    if request.method == 'POST':

        nric = helper.remove_symbol(request.form['nric'])
        password = str(request.form['password'])

        patient = UserData(nric, create=False)
        if patient.exist():
            flash("That patient already exist!")
            return redirect(url_for("doc_patient"))

        f_name = helper.remove_symbol(request.form['f_name'])
        l_name = helper.remove_symbol(request.form['l_name'])

        email = str(request.form['email'])
        contact = helper.remove_symbol(request.form['contact'])

        gender = helper.remove_symbol(request.form['gender'])
        blood = helper.remove_symbol(request.form['blood'])

        verify = helper.check_form(user, nric, f_name, l_name, gender, blood)
        if not verify[0]:
            flash(verify[1])
            return redirect(url_for("doc_patient"))

        verify_pass = helper.password_check(password)
        if not verify_pass[0]:
            flash(verify_pass[1])
            return redirect(url_for("doc_patient"))

        patient = UserData(nric, create=True)

        patient.set_password(password)
        patient.set_user_level(UserData.USR_PATIENTS)
        patient.set_doctor(user.id())

        patient.details.set_nric(nric)
        patient.details.set_fname(f_name)
        patient.details.set_lname(l_name)
        patient.details.set_email(email)
        patient.details.set_contact(contact)
        patient.details.set_gender(gender)
        patient.details.set_blood(blood)

        db.Commit()

        flash("Added a new paitient!")
        return redirect(url_for("doc_patient"))

    return render_template("panel/doctor/add_patient.html")


@app.route('/panel/doctor/consultations', methods=['GET', 'POST'])
def doc_consultations():

    logger.create_view(request)

    user = access_control(doc_consultations.__name__)
    if type(user) != UserData:
        return user
    
    if request.method == 'POST':

        nric = str(request.form['nric'])
        c_time = str(request.form['c_time'])
        c_date = str(request.form['c_date'])
        comments = str(request.form['comments'])
        block = str(request.form['block'])
        unit = str(request.form['unit'])
        department = str(request.form['department'])

        patient = UserData(nric, create=False)
        if not patient.exist():
            flash("That patient does not exist!")
            return redirect(url_for("consultations"))
        
        patient.consultation.create_consultation(c_time, c_date, comments, block, unit, department, user.id())
        flash("Consultation record has been created!")

    return render_template("panel/doctor/consultations.html")


@app.route('/panel/doctor/patients/view', methods=['GET', 'POST'])
def doc_view():

    logger.create_view(request)

    user = access_control(doc_view.__name__)
    if type(user) != UserData:
        return user

    if request.method == 'POST':

        type_id = str(request.form['type'])
        userid = str(request.form['userid'])

        if type_id == "update":
            return redirect(url_for("doc_update"))

        if type_id == "delete":

            patient = UserData(userid=userid)
            patient.self_delete()
            
            flash("The patient has been removed!")
            return redirect(url_for("doc_view"))
    
    search = request.args.get("search")
    
    if search:
        
        all_users = []
        search = helper.remove_symbol(search)
        
        if helper.verify_nric(search):
            
            patient = UserData(search, create=False)
            if patient.exist() and patient.get_user_level() == UserData.USR_PATIENTS:
                all_users.append(patient)

        else:
            search = None
            flash("Please enter a valid NRIC")

    else:
        limit = site.get_max_pat()
        r_users = db.Retrieve("user_info")
        all_users = []

        for x in range(len(r_users)):
            cur_user = UserData(userid=r_users[x][0])

            if cur_user.get_user_level() == UserData.USR_PATIENTS:
                all_users.append(cur_user)
            
            if len(all_users) >= limit:
                break

    return render_template("panel/doctor/patients.html", patients=all_users, search=search)


@app.route('/panel/users/update/<user_id>', methods=['GET', 'POST'])
def doc_update(user_id):        

    user = access_control(doc_update.__name__)
    if type(user) != UserData:
        return user

    patient = UserData(userid=user_id, create=False)

    if not patient.exist():
        flash("The user does not exist!")
        return redirect(url_for("doc_view"))

    if request.method == 'POST':

        f_name = str(request.form['f_name'])
        l_name = str(request.form['l_name'])

        gender = str(request.form['gender'])
        blood = str(request.form['blood'])

        contact = str(request.form['contact'])
        email = str(request.form['email'])

        height = str(request.form['height'])
        weight = str(request.form['weight'])

        dob = str(request.form['dob'])

        patient.details.set_fname(f_name)
        patient.details.set_lname(l_name)

        patient.details.set_gender(gender)
        patient.details.set_blood(blood)

        patient.details.set_contact(contact)
        patient.details.set_email(email)

        patient.details.set_height(height)
        patient.details.set_weight(weight)

        patient.details.set_dob(dob)

        flash("The user details has been updated!")

    return render_template("panel/doctor/update_patient.html", paitent=patient)


@app.route('/panel/doctor/upload/images', methods=['GET', 'POST'])
def doc_upload_images():

    user = access_control(doc_upload_images.__name__)
    if type(user) != UserData:
        return user

    if  request.method == 'POST':
        
        if not recaptcha.verify():
            flash("Please fill out the ReCaptcha!")
            return redirect(url_for("index"))

        nric = str(request.form['nric'])
        catergory = str(request.form['scan_type'])
        description = str(request.form['description'])
        time_taken = str(request.form['time_taken'])

        patient = UserData(NRIC=nric, create=False)

        if not patient.exist():
            flash("The user does not exist!")
            return redirect(url_for("doc_upload_images"))

        if 'image' in request.files:
            file = request.files['image']

            if file.filename != '' and file:

                if helper.allowed_file(file.filename):
                    patient.images.create_image(catergory, image=file.read(), description=description, doctor=user.id(), time_taken=time_taken)
                    flash("Image has been successfully uploaded!")
                else:
                    flash("The extention of the image you uploaded is no allowed!")

    return render_template("panel/doctor/upload_images.html")


@app.route('/panel/view/patients/<uid>', methods=['GET'])
def doc_view_patients(uid):
    
    logger.create_view(request)

    user = access_control(doc_view_patients.__name__)
    if type(user) != UserData:
        return user

    view_user = UserData(userid=uid, create=False)

    if not view_user.exist():
        flash("The user does not exist!")
        return redirect(url_for("panel"))

    print(view_user.images.retrive_images())

    return render_template("panel/doctor/view_user.html", user=view_user, sys_consultation=view_user.consultation, consultation=view_user.consultation.retrieve_consultation(), sys_images=view_user.images, images=view_user.images.retrive_images())

#######################
#    PANEL/ADMINS     #
#######################
@app.route('/panel/admin/purge', methods=['GET', 'POST'])
def admin_purge():

    logger.create_view(request)

    user = access_control(admin_purge.__name__)
    if type(user) != UserData:
        return user

    if request.method == 'POST':

        if "purge_dur" not in request.form or "purge_type" not in request.form:
            flash("Something went wrong, please try again later!")
            return redirect(url_for("panel"))

        purge_dur = int(request.form['purge_dur'])
        purge_type = str(request.form['purge_type'])
        purge_level = int(request.form['purge_level'])
        
        if purge_type == "user":
            user_manager.purge_users(purge_dur, purge_level)
        elif purge_type == "logs":
            logger.purge_logs(purge_dur)

        flash(f"Purged {purge_type} lasting for {purge_dur} seconds!")
        return redirect(url_for("panel"))

    else:
        flash("Something went wrong! Try again later")
        return redirect(url_for("panel"))


@app.route('/panel/admin/users/patients', methods=['GET', 'POST'])
def admin_patients():

    logger.create_view(request)

    user = access_control(admin_patients.__name__)
    if type(user) != UserData:
        return user

    
    if request.method == 'POST':

        type_id = str(request.form['type'])
        userid = str(request.form['userid'])

        if type_id == "delete":

            patient = UserData(userid=userid)
            patient.self_delete()
            
            flash("The patient has been removed!")
            return redirect(url_for("admin_patients"))

    search = request.args.get("search")
    
    if search:
        
        all_users = []
        search = helper.remove_symbol(search)
        
        if helper.verify_nric(search):
            
            patient = UserData(NRIC=search, create=False)
            if patient.exist() and patient.get_user_level() == UserData.USR_PATIENTS:
                all_users.append(patient)

        else:
            search = None
            flash("Please enter a valid NRIC")

    else:
        limit = site.get_max_pat()
        r_users = db.Retrieve("user_info")
        all_users = []
        
        for x in range(len(r_users)):
            cur_user = UserData(userid=r_users[x][0])

            if cur_user.get_user_level() == UserData.USR_PATIENTS:
                all_users.append(cur_user)
            
            if len(all_users) >= limit:
                break

    return render_template("panel/admin/patients.html", all_users=all_users, search=search)


@app.route('/panel/admin/users/doctor', methods=['GET', 'POST'])
def admin_doctors():

    logger.create_view(request)

    user = access_control(admin_doctors.__name__)
    if type(user) != UserData:
        return user

    if request.method == 'POST':

        type_id = str(request.form['type'])
        userid = str(request.form['userid'])

        if type_id == "delete":

            doctor = UserData(userid=userid)
            doctor.self_delete()
            
            flash("The doctor has been removed!")
            return redirect(url_for("admin_doctors"))
    
    search = request.args.get("search")
    
    if search:
        
        all_users = []
        search = helper.remove_symbol(search)
        
        if helper.verify_nric(search):
            
            patient = UserData(search, create=False)
            if patient.exist() and patient.get_user_level() == UserData.USR_DOCTOR:
                all_users.append(patient)

        else:
            search = None
            flash("Please enter a valid NRIC")

    else:
        limit = site.get_max_pat()
        r_users = db.Retrieve("user_info")
        all_users = []

        for x in range(len(r_users)):
            cur_user = UserData(userid=r_users[x][0])

            if cur_user.get_user_level() == UserData.USR_DOCTOR:
                all_users.append(cur_user)
            
            if len(all_users) >= limit:
                break

    return render_template("panel/admin/doctors.html", all_users=all_users, search=search)


@app.route('/panel/admin/users/admins', methods=['GET', 'POST'])
def admin_admins():

    logger.create_view(request)

    user = access_control(admin_admins.__name__)
    if type(user) != UserData:
        return user

    if request.method == 'POST':

        type_id = str(request.form['type'])
        userid = str(request.form['userid'])

        if type_id == "delete":

            admin = UserData(userid=userid)
            admin.self_delete()
            
            flash("The admin has been removed!")
            return redirect(url_for("admin_admins"))

    search = request.args.get("search")
    
    if search:
        
        all_users = []
        search = helper.remove_symbol(search)
        
        if helper.verify_nric(search):
            
            patient = UserData(search, create=False)
            if patient.exist() and patient.get_user_level() == UserData.USR_ADMINS:
                all_users.append(patient)

        else:
            search = None
            flash("Please enter a valid NRIC")

    else:
        limit = site.get_max_pat()
        r_users = db.Retrieve("user_info")
        all_users = []
        
        for x in range(len(r_users)):
            cur_user = UserData(userid=r_users[x][0])

            if cur_user.get_user_level() == UserData.USR_ADMINS:
                all_users.append(cur_user)
            
            if len(all_users) >= limit:
                break

    return render_template("panel/admin/admins.html", all_users=all_users, search=search)


@app.route('/panel/admins/all_user/add', methods=['GET', 'POST'])
def admin_create():

    logger.create_view(request)

    user = access_control(admin_create.__name__)
    if type(user) != UserData:
        return user

    if request.method == 'POST':

        nric = helper.remove_symbol(request.form['nric'])
        password = str(request.form['password'])
        user_level = int(request.form['user_level'])

        user = UserData(nric)
        if user.exist() or user.is_valid():
            flash("The user you are trying to create already exist!")
            return redirect(url_for("admin_create"))

        f_name = helper.remove_symbol(request.form['f_name'])
        l_name = helper.remove_symbol(request.form['l_name'])
        gender = helper.remove_symbol(request.form['gender'])

        verify = helper.check_form(user, nric, f_name, l_name, gender)
        if not verify[0]:
            flash(verify[1])
            return redirect(url_for("admin_create"))

        new_user = UserData(nric, create=True)

        new_user.set_password(password)
        new_user.set_user_level(user_level)

        new_user.details.set_nric(nric)
        new_user.details.set_fname(f_name)
        new_user.details.set_lname(l_name)
        new_user.details.set_gender(gender)

        db.Commit()

        flash("Added a new user!")
        return redirect(url_for("admin_create"))


    return render_template("panel/admin/add_users.html")


@app.route('/panel/admin/backup', methods=['GET', 'POST'])
def admin_backup():

    logger.create_view(request)

    user = access_control(admin_backup.__name__)
    if type(user) != UserData:
        return user

    if request.method == 'POST':

        action = str(request.form['type'])

        if action == "create":
            db.Backup()

            flash("A new backup has been created!")

        elif action == "restore":

            backupid = str(request.form['backupid'])
            db.RestoreBackup(backupid)

            flash("Database has been restored")

        elif action == "delete":

            backupid = str(request.form['backupid'])
            db.DeleteBackup(backupid)

            flash("Database has been deleted")

        
        return redirect(url_for("admin_backup"))
        

    backups = os.listdir(config["database"]["backup"])
    return render_template("panel/admin/backup.html", backups=backups)


@app.route('/panel/admin/logs', methods=['GET', 'POST'])
def admin_logs():

    logger.create_view(request)

    user = access_control(admin_logs.__name__)
    if type(user) != UserData:
        return user

    limit = site.get_max_log() - 1
    log_level = request.args.get('log_level')

    if log_level:
        all_logs = logger.retrieve_logs(log_level)
    else:
        r_logs = db.GetLastFew("log_detail", limit=limit)

        all_logs = []
        
        for x in range(len(r_logs)):
            curr_log = LoggingData(logid=r_logs[x])
            all_logs.append(curr_log)

    return render_template("panel/admin/logging.html", all_logs=all_logs)


@app.route('/panel/admin/site/settings', methods=['GET', 'POST'])
def admin_site_settings():

    logger.create_view(request)

    user = access_control(admin_site_settings.__name__)
    if type(user) != UserData:
        return user

    if request.method == 'POST':

        set_type = str(request.form["set_type"])
        if set_type == "items":

            max_log = int(request.form['max_log'])
            site.set_max_log(max_log)

            max_pat = int(request.form['max_pat'])
            site.set_max_pat(max_pat)

            flash("Item display settings has been saved!")
        
        elif set_type == "database":
            
            pass_hash = str(request.form['pass_hash'])
            userbase_hash = str(request.form['userbase_hash'])
            database_hash = str(request.form['database_hash'])
            id_length = str(request.form['id_length'])

            userid_masking = str(request.form['userid_masking'])
            encryption_keyiv = str(request.form['encryption_keyiv'])
            hashing_layers = str(request.form['hashing_layers'])
            salt_length = str(request.form['salt_length'])

            encryption_key = str(request.form['encryption_key'])
            user_encryption = str(request.form['user_encryption'])
            user_detail_encryption = str(request.form['user_detail_encryption'])
            consultations_encryption = str(request.form['consultations_encryption'])
            log_encryption = str(request.form['log_encryption'])
            images_encryption = str(request.form['images_encryption'])
            blog_encryption = str(request.form['blog_encryption'])

            if not user_encryption in encryption.encrypting.encryption:
                flash("User table encryption is Invalid!")
                return redirect(url_for("admin_site_settings"))
            
            if not user_detail_encryption in encryption.encrypting.encryption:
                flash("User Detail table encryption is Invalid!")
                return redirect(url_for("admin_site_settings"))
            
            if not consultations_encryption in encryption.encrypting.encryption:
                flash("Consultation table encryption is Invalid!")
                return redirect(url_for("admin_site_settings"))

            if not log_encryption in encryption.encrypting.encryption:
                flash("Logging table encryption is Invalid!")
                return redirect(url_for("admin_site_settings"))

            if not images_encryption in encryption.encrypting.encryption:
                flash("Image table encryption is Invalid!")
                return redirect(url_for("admin_site_settings"))

            if not blog_encryption in encryption.encrypting.encryption:
                flash("Blog table encryption is Invalid!")
                return redirect(url_for("admin_site_settings"))


            if not pass_hash in encryption.hashing.hashes:
                flash("Password Hash is Invalid!")
                return redirect(url_for("admin_site_settings"))
            
            if not userbase_hash in encryption.hashing.hashes:
                flash("User Data Hash is Invalid!")
                return redirect(url_for("admin_site_settings"))
            
            if not database_hash in encryption.hashing.hashes:
                flash("Database Hash is Invalid!")
                return redirect(url_for("admin_site_settings"))
            
            site.set_database_hash(database_hash)
            site.set_pass_hash(pass_hash)
            site.set_userbase_hash(userbase_hash)
            site.set_id_length(id_length)
            site.set_userid_masking(userid_masking)
            site.set_encryption_keyiv(encryption_keyiv)
            site.set_hashing_layers(hashing_layers)
            site.set_salt_length(salt_length)

            site.set_encryption_key(encryption_key)
            site.set_user_encryption(user_encryption)
            site.set_user_detail_encryption(user_detail_encryption)
            site.set_consultations_encryption(consultations_encryption)
            site.set_log_encryption(log_encryption)
            site.set_images_encryption(images_encryption)
            site.set_blog_encryption(blog_encryption)

            db.CloseConnection()
            db.SelfDestruct()

            if os.path.isfile(config["database"]["path"]):
                flash("Unable to remove the existing database!")
                return redirect(url_for("admin_site_settings"))
            
            flash("Database encryption settings saved!")
        
        elif set_type == "rention":

            user_rention = str(request.form['user_rention'])
            image_rention = str(request.form['image_rention'])
            consultation_rention = str(request.form['consultation_rention'])

            site.set_user_rention(user_rention)
            site.set_image_rention(image_rention)
            site.set_consultation_rention(consultation_rention)
            
            flash("Data rention settings saved!")

    
    return render_template("panel/admin/site_settings.html", site=site, hashes=encryption.hashing.hashes, encryption=encryption.encrypting.encryption)


@app.route('/settings/systeminformation')
def admin_system_information():

    logger.create_view(request)

    user = access_control(admin_system_information.__name__)
    if type(user) != UserData:
        return user

    info = {}
    info['Platform'] = platform.system()
    info['Platform Release'] = platform.release()
    info['Platform Version'] = platform.version()
    info['Architecture'] = platform.machine()
    info['Hostname'] = socket.gethostname()
    info['IP Address'] = socket.gethostbyname(socket.gethostname())
    info['Processor'] = platform.processor()
    info['RAM'] = str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + " GB"

    cpu_info = {}
    cpu_info["Physical Cores"] = str(psutil.cpu_count(logical=False))
    cpu_info["Total Cores"] = psutil.cpu_count(logical=True)

    # CPU frequencies
    cpufreq = psutil.cpu_freq()
    cpu_info["Max Frequency"] = str(f"{cpufreq.max:.2f}Mhz")
    cpu_info["Min Frequency"] = str(f"{cpufreq.min:.2f}Mhz")
    cpu_info["Current Frequency"] = str(f"{cpufreq.current:.2f}Mhz")
    cpu_info["Total CPU Usage"] = str(psutil.cpu_percent()) + "%"

    memory_info = {}
    svmem = psutil.virtual_memory()
    memory_info["Total"] = (f"{helper.get_size(svmem.total)}")
    memory_info["Available"] = (f"{helper.get_size(svmem.available)}")
    memory_info["Used"] = (f"{helper.get_size(svmem.used)}")
    memory_info["Percentage"] = (f"{svmem.percent}%")


    return render_template('panel/admin/systeminformation.html', info=info, cpu_info=cpu_info, memory_info=memory_info)



@app.route('/blogs/create', methods=['GET', 'POST'])
def admin_blogs_create():

    logger.create_view(request)

    user = access_control(admin_blogs_create.__name__)
    if type(user) != UserData:
        return user

    if request.method == 'POST':

        post_title = str(request.form['post_title'])
        author = str(request.form['author'])
        category = str(request.form['category'])
        content = str(request.form['content'])

        if 'image' in request.files:
            file = request.files['image']

            if file.filename != '' and file:
                if helper.allowed_file(file.filename):
                    user.blogs.create_blog(post_title, author, content, file.read(), category)
                    flash("Blog post has been created!")
                else:
                    flash("The extention of the image you uploaded is no allowed!")
                    return redirect(url_for("admin_blogs_create"))
        
        flash("The blog post has been uploaded!")

    return render_template('panel/admin/blogs_create.html')


@app.route('/panel/admin/view/blogs', methods=['GET', 'POST'])
def admin_view_blogs():
    
    logger.create_view(request)

    user = access_control(admin_view_blogs.__name__)
    if type(user) != UserData:
        return user
    
    if request.method == 'POST':

        action = str(request.form['type'])

        if action ==  "delete":
            blogid = str(request.form['blogid'])
            blog = user.blogs.retrive_blog(blogid)
            blog.self_delete()
            
            flash("Blog post has been deleted!")


    blogs = user.blogs.retrive_blogs()
    return render_template("panel/admin/blogs.html", blogs=blogs)


@app.route('/panel/admin/view/blogs/edit/<blogid>', methods=['GET', 'POST'])
def admin_edit_blogs(blogid):
    
    logger.create_view(request)

    user = access_control(admin_edit_blogs.__name__)
    if type(user) != UserData:
        return user
    
    if request.method == 'POST':

        post_title = str(request.form['post_title'])
        author = str(request.form['author'])
        category = str(request.form['category'])
        content = str(request.form['content'])
        image = None

        if 'image' in request.files:
            file = request.files['image']

            if file.filename != '' and file:
                if helper.allowed_file(file.filename):
                    image = file.read()
                else:
                    flash("The extention of the image you uploaded is no allowed!")
                    return redirect(url_for("admin_blogs_create"))
        
        user.blogs.update_blog(blogid=blogid, post_title=post_title, author=author, content=content, image=image, category=category)

    blog = user.blogs.retrive_blog(blogid=blogid)
    return render_template("panel/admin/blogs_edit.html", blog=blog)


@app.route('/panel/admin/view/access/control', methods=['GET', 'POST'])
def admin_view_access():
    
    logger.create_view(request)

    user = access_control(admin_view_access.__name__)
    if type(user) != UserData:
        return user
    
    if request.method == 'POST':

        for v in request.form:
            
            access = site.get_access_control()
            if v in access:

                user_level = str(request.form.getlist(v))
                site.set_access_control_url(v, user_level)
        
        flash("Settings has been updated!")
        return redirect(url_for("admin_view_access"))

    return render_template("panel/admin/access_control.html", access=site.get_access_control())