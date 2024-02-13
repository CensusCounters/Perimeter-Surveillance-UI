import cv2
from flask import render_template, url_for, redirect, request, session, make_response, Response
from finalfrsproject import app, ALLOWED_PHOTO_EXTENSIONS, sqlCommands, jwt, routeMethods, redisCommands
import os, shutil, sys
from datetime import datetime, time, timedelta
import uuid
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt, jwt_required, set_access_cookies, \
    unset_jwt_cookies
import json
import pandas as pd


# Login
@app.route("/", methods=['GET'])
@app.route("/login", methods=['GET', 'POST'])
def login():
    print("In Login: ", request.method)
    try:
        if request.method == 'POST':
            form = request.form
            print("form: ", form)
            if form.get('username') and form.get('password'):
                result = sqlCommands.login(form.get('username'), form.get('password'))

                if not result or result.get('Status') == "Fail" or result is None or len(result) == 0:
                    print("Login unsuccessful")
                    send_to_html_json = {
                        'message': 'Login information incorrect. Please check the username and password entered.',
                        'page_title': "Login"
                    }
                    return render_template('login.html', details=send_to_html_json)

                else:
                    result = result.get("Details")
                    print("Login successful: ", result)

                    logged_in_user_name = result[0]
                    logged_in_user_type = result[1]
                    logged_in_user_id = result[2]
                    application_name = "platform_ui"
                    redis_parent_key = str(logged_in_user_id) + application_name

                    identity = {
                        "logged_in_user_name": logged_in_user_name,
                        "logged_in_user_type": logged_in_user_type,
                        "logged_in_user_id": logged_in_user_id,
                        "redis_parent_key": redis_parent_key,
                        "application_name": application_name
                    }
                    access_token = create_access_token(identity=identity)
                    # access the redis object if available

                    destination = None
                    if redisCommands.redis_conn.get(redis_parent_key) is not None:
                        #redisCommands.redis_conn.delete(redis_parent_key)
                        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))
                        print("redis in login: ", session_values_json_redis)
                        if session_values_json_redis.get("ticket_status") is not None:
                            destination = session_values_json_redis.get("ticket_status")
                            print("redis in login destination: ", destination)
                        else:
                            print("redis in login: no ticket status")
                            destination = "home"
                            print("redis in login destination: ", destination)
                    else:
                        print("redis in login not available")
                        destination = "home"
                        print("redis in login destination: ", destination)

                    response = make_response(redirect(url_for(destination)))
                    set_access_cookies(response, access_token)
                    return response

            else:
                print("No username and password in login")
                send_to_html_json = {
                    'message': 'Welcome. Please login with your name and password to continue.',
                    'page_title': "Login"
                }
                return render_template('login.html', details=send_to_html_json)

        # GET
        else:
            send_to_html_json = {
                'message': 'Welcome. Please login with your name and password to continue.',
                'page_title': "Login"
            }
            return render_template('login.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in login of", fname, "at line number", exc_tb.tb_lineno, ":", error)

        send_to_html_json = {
            'message': "An unexpected error has happened. The administration has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        # print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500

    # Logout


@app.route("/logout", methods=['GET', 'POST'])
@jwt_required()
def logout():
    print("In Logout: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = None

        # POST
        if request.method == 'POST':
            if redisCommands.redis_conn.get(redis_parent_key) is not None:
                session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

            form = request.form

            if form.get('Yes') == 'Yes':
                print('redis in logout when save redis is selected: ', session_values_json_redis)
                response = make_response(redirect(url_for('login')))
                unset_jwt_cookies(response)
                return response

            else:
                redisCommands.redis_conn.delete(redis_parent_key)
                if redisCommands.redis_conn.get(redis_parent_key) is not None:
                    session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))
                    print('redis in logout when delete redis is selected: ', session_values_json_redis)
                else:
                    print('redis in logout after redis is deleted')
                response = make_response(redirect(url_for('login')))
                unset_jwt_cookies(response)
                return response
        # GET
        else:
            message = 'Do you want to save the current progress and start from this point next time you log in?'
            send_to_html_json = {
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': message,
                'page_title': 'Logout'
            }
            return render_template('logout.html', details=send_to_html_json)


    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in logout of", fname, "at line number", exc_tb.tb_lineno, ":", error)

        send_to_html_json = {
            'message': "An unexpected error has happened. The administration has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        # print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500

    # Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


# Home
@app.route("/home", methods=['GET', 'POST'])
@jwt_required()
def home():
    print("In Home: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        ticket_id = uuid.uuid4()
        ticket_start_time = datetime.now()
        logged_in_user_id = jwt_details.get('logged_in_user_id')

        # POST
        if request.method == 'POST':

            if redisCommands.redis_conn.get(redis_parent_key) is not None:
                session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))
                redisCommands.redis_conn.delete(redis_parent_key)

            form = request.form
            print("form: ", form)
            if form.get('add_camera'):
                ticket_status = "add_camera"
                session_values_json_redis = {
                    "ticket_id": str(ticket_id),
                    "ticket_start_time": str(ticket_start_time),
                    "ticket_status": ticket_status,
                    "logged_in_user_id": logged_in_user_id
                }
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                print('redis in home when new camera is selected: ', session_values_json_redis)

                return redirect(url_for('add_camera'))

            elif form.get('edit_camera'):
                ticket_status = "list_camera"
                session_values_json_redis = {
                    "ticket_id": str(ticket_id),
                    "ticket_start_time": str(ticket_start_time),
                    "ticket_status": ticket_status,
                    "logged_in_user_id": logged_in_user_id
                }
                print('redis in home when edit camera is selected: ', session_values_json_redis)
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                return redirect(url_for('list_camera'))

            elif form.get('view_reports'):
                ticket_status = "report_home"
                session_values_json_redis = {
                    "ticket_id": str(ticket_id),
                    "ticket_start_time": str(ticket_start_time),
                    "ticket_status": ticket_status,
                    "logged_in_user_id": logged_in_user_id
                }
                print('redis in home when report is selected: ', session_values_json_redis)
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                return redirect(url_for('report_home'))
            else:
                print('calling home.html. no redis: ')
                send_to_html_json = {
                    'logged_in_user': jwt_details.get("logged_in_user_name"),
                    'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                    'message': 'Please click on one of the options below to continue.',
                    'page_title': 'Home Page'
                }
                return render_template('home.html', details=send_to_html_json)

        # GET
        else:
            # remove any objects in redis
            if redisCommands.redis_conn.get(redis_parent_key) is not None:
                session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))
                redisCommands.redis_conn.delete(redis_parent_key)
                print('redis in home before Get method: ', session_values_json_redis)
            else:
                print('no redis in home: ')
            send_to_html_json = {
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': 'Please click on one of the options below to continue. This will start a new thread.',
                'page_title': 'Home Page'
            }
            return render_template('home.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in home of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administration has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        return render_template('500.html', details=send_to_html_json), 500


@app.route("/stop_processing", methods=['GET', 'POST'])
@jwt_required()
def stop_processing():
    print("In stop_processing: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redis_parent_key)
        message = session_values_json_redis.get('message')

        # POST
        if request.method == 'POST':
            session_values_json_redis.update({"ticket_status": "home"})
            redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
            print('redis in stop_processing before redirecting to home: ', session_values_json_redis)
            return redirect(url_for('home'))

            # GET
        else:
            send_to_html_json = {
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': message,
                'page_title': 'Error'
            }
            return render_template('stop_processing.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in stop_processing of", fname, "at line number", exc_tb.tb_lineno, ":", error)

        send_to_html_json = {
            'message': "An unexpected error has happened. The administrator has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        return render_template('500.html', details=send_to_html_json), 500

    # Using an `after_request` callback, we refresh any token that is within 30 datetime


# minutes of expiring. Change the timedeltas to match the needs of your application.
@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now()
        target_timestamp = datetime.timestamp(now + timedelta(minutes=10))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response


@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    session.clear()
    response = make_response(redirect(url_for('login')))
    unset_jwt_cookies(response)
    return response


# Add Camera
@app.route("/add_camera", methods=['GET', 'POST'])
@jwt_required()
def add_camera():
    print("In add_camera: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

        # POST
        if request.method == 'POST':
            form = request.form
            print('form: ', form)
            camera_make = form.get('camera_type')
            camera_ip = form.get('camera_ip')
            camera_username = form.get('camera_username')
            camera_password = form.get('camera_password')
            if camera_make == 'HikVision':
                # rtsp: // username:password@< address >: < port > / Streaming / Channels / < id >
                camera_rtsp_address = "rtsp://" + camera_username + ":" + camera_password + "@" + camera_ip + ":554/Streaming/Channels/101"
            elif camera_make == 'Prama':
                camera_rtsp_address = "rtsp://" + camera_username + ":" + camera_password + "@" + camera_ip + ":554/Streaming/Channels/101"
            elif camera_make == 'Dahua':
                # rtsp://<username>:<password>@<ip>:<port>/cam/realmonitor?channel=<channelNo>&subtype=<typeNo>
                camera_rtsp_address = "rtsp://" + camera_username + ":" + camera_password + "@" + camera_ip + ":554/cam/realMonitor?channel=1&subtype=1"
            elif camera_make == "CPPlus":
                # rtsp://< user >: < pass >@< cameraip >: < port > / cam / realmonitor?channel = 1 & subtype = 0
                camera_rtsp_address = "rtsp://" + camera_username + ":" + camera_password + "@" + camera_ip + ":554/cam/realMonitor?channel=1&subtype=1"
            else:
                camera_rtsp_address = "rtsp://ec2-13-235-48-204.ap-south-1.compute.amazonaws.com:8554/stream1"
                # camera_rtsp = "rtsp://rtspstream:26d9ae61eaffdb00d6acc9f30e03ad3f@zephyr.rtsp.stream/pattern"

            print("rtsp: ", camera_rtsp_address)
            session_values_json_redis.update({"camera_make": camera_make})
            session_values_json_redis.update({"camera_ip_address": camera_ip})
            session_values_json_redis.update({"camera_username": camera_username})
            session_values_json_redis.update({"camera_password": camera_password})
            session_values_json_redis.update({"camera_rtsp_address": camera_rtsp_address})
            camera_associated_services = ["MOG2", "People_Detection"]
            session_values_json_redis.update({"camera_associated_services": camera_associated_services})
            redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
            print("redis in add camera: ", session_values_json_redis)
            message = 'Success! Camera is now connected. Please click continue to proceed. '
            send_to_html_json = {
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': message,
                'page_title': "View Camera"
            }
            return render_template('view_camera.html', details=send_to_html_json)
        # GET
        else:
            session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))
            if session_values_json_redis.get("message") is not None:
                message = session_values_json_redis.get("message")
            else:
                message = 'Please provide the camera details in the form and click Submit.'
            send_to_html_json = {
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': message,
                'page_title': "Add a New Camera"
            }
            return render_template('add_camera.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in add_camera of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administratior has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


@app.route("/view_camera", methods=['GET', 'POST'])
@jwt_required()
def view_camera():
    print("In view_camera: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))
        camera_rtsp_address = None

        # POST
        if request.method == 'POST':
            form = request.form
            print('form: ', form)
            if form.get('continue'):
                #get a frame from opencv and save it to the hard drive
                #save the image location in redis
                #use that image in the canvas
                if session_values_json_redis.get('camera_rtsp_address'):
                    camera_rtsp_address = session_values_json_redis.get('camera_rtsp_address')
                elif session_values_json_redis.get('camera_to_be_edited'):
                    camera_to_edit = session_values_json_redis.get('camera_to_be_edited')
                    camera_rtsp_address = camera_to_edit[0].get("camera_rtsp_address")
                print("rtsp: ", camera_rtsp_address)
                camera = cv2.VideoCapture(camera_rtsp_address, cv2.CAP_FFMPEG)
                person_image_actual_path = os.path.sep.join([app.config['IMAGE_UPLOADS'], "frame.jpg"])

                frame_count = 0
                success = True
                while success:
                    success, image = camera.read()
                    frame_count += 1
                    if frame_count == 25:
                        cv2.imwrite(person_image_actual_path, image)
                        break
                person_image_html_path = os.path.sep.join([app.config["IMAGE_PATH_FOR_HTML"], os.path.basename(person_image_actual_path)])
                print('actual path: ', person_image_actual_path)
                print('html path: ', person_image_html_path)
                session_values_json_redis.update({"image_html_path": person_image_html_path})
                session_values_json_redis.update({"ticket_status": "add_region_of_interest"})
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                print("redis in view camera: ", session_values_json_redis)
                return redirect(url_for('add_region_of_interest'))

        # GET
        else:
            if session_values_json_redis.get('camera_rtsp_address'):
                camera_rtsp_address = session_values_json_redis.get('camera_rtsp_address')
            elif session_values_json_redis.get('camera_to_be_edited'):
                camera_to_edit = session_values_json_redis.get('camera_to_be_edited')
                camera_rtsp_address = camera_to_edit[0].get("camera_rtsp_address")
            print("rtsp: ", camera_rtsp_address)
            camera = cv2.VideoCapture(camera_rtsp_address, cv2.CAP_FFMPEG)
            return Response(routeMethods.generate_frames(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in view_camera of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administrator has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


@app.route("/add_region_of_interest", methods=['GET', 'POST'])
@jwt_required()
def add_region_of_interest():
    print("In add_region_of_interest: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

        # POST
        if request.method == 'POST':
            form = request.form
            print('form: ', form)
            if form.get('region_of_interest'):
                camera_region_of_interest = json.loads(form.get('region_of_interest'))
                session_values_json_redis.update({"camera_region_of_interest": camera_region_of_interest})
                print("camera_region_of_interest: ", camera_region_of_interest)

            if form.get('roi_type'):
                roi_type = form.get('roi_type')
                if roi_type == 'Include':
                    roi_type = 'True'
                else:
                    roi_type = 'False'
                session_values_json_redis.update({"camera_roi_type": roi_type})
                print("roi_type: ", roi_type)

            redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
            # save the values received in the form to the database
            result = routeMethods.insert_new_camera_record(session_values_json_redis)
            if not result or result.get('Status') == "Fail" or result.get("Insert_Count") == 0:
                session_values_json_redis.update(
                    {"message": "System was unable to insert a camera record. Please try again."})
                session_values_json_redis.update({"ticket_status": "add_camera"})
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                print("insert a camera record failed")
                print("redis in view_stream on insert new camera fail: ", session_values_json_redis)
                send_to_html_json = {
                    'message': "System was unable to insert a camera record. Please try again",
                    'page_title': "Error"
                }
                return render_template('500.html', details=send_to_html_json), 500
            else:
                details = result.get('Details')
                session_values_json_redis.update({"message": "New camera successfully added to the database."})
                session_values_json_redis.update({"ticket_status": "home"})
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                print('redis in add_region_of_interest on insert new camera success: ', session_values_json_redis)
                send_to_html_json = {
                    'message': "New camera successfully added to the database. Press Continue to proceed.",
                    'page_title': "Success"
                }
                return render_template('success_page.html', details=send_to_html_json), 500

        # GET
        else:
            message = 'Please click on the Region of Interest to draw a region of interest or click Continue to proceed without it.'
            image_html_path = session_values_json_redis.get('image_html_path')
            send_to_html_json = {
                'image': image_html_path,
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': message,
                'page_title': "Add Region Of Interest"
            }
            return render_template('add_region_of_interest.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in add_region_of_interest of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administrator has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500




# List Cameras
@app.route("/list_camera", methods=['GET', 'POST'])
@jwt_required()
def list_camera():
    print("In list_camera: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

        # POST
        if request.method == 'POST':
            form = request.form
            print("form: ", form)
            camera_id = form.get("camera_id")
            result = sqlCommands.get_camera_details(camera_id)

            if not result or result.get('Status') == "Fail" or len(result.get("Details")) == 0:
                session_values_json_redis.update(
                    {"message": "System was unable to retrieve camera details for camera id: " + camera_id + ". Please try again."})
                session_values_json_redis.update({"ticket_status": "list_camera"})
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                print("get camera details failed")
                send_to_html_json = {
                    'message': "System was unable to retrieve camera details for camera id: " + camera_id + ". Please try again.",
                    'page_title': "Error"
                }
                return render_template('500.html', details=send_to_html_json), 500

            else:
                camera_details = result.get("Details")
                print('result ', type(camera_details))
                print('result ', camera_details)
                camera_to_edit = [{
                    'camera_make': camera_details.get("camera_make"),
                    'camera_ip_address': camera_details.get("camera_ip_address"),
                    'camera_username': camera_details.get("camera_username"),
                    'camera_password': camera_details.get("camera_password"),
                    'camera_rtsp_address': camera_details.get("camera_rtsp_address"),
                    'camera_region_of_interest': camera_details.get("camera_region_of_interest"),
                    'camera_associated_services': camera_details.get("camera_associated_services"),
                    'camera_id': camera_details.get("id")
                }]
                session_values_json_redis.update({'camera_to_be_edited': camera_to_edit})
                session_values_json_redis.update({"ticket_status": "edit_camera_details"})
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                return redirect(url_for('edit_camera_details'))
        # GET
        else:
            result = sqlCommands.get_camera_list()

            if not result or result.get('Status') == "Fail":
                session_values_json_redis.update(
                    {"message": "System was unable to retrieve the camera list. Please try again."})
                session_values_json_redis.update({"ticket_status": "home"})
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                print("get camera list failed")
                print("redis in list_camera on insert new camera fail: ", session_values_json_redis)
                send_to_html_json = {
                    'message': "System was unable to retrieve the camera list. Please try again",
                    'page_title': "Error"
                }
                return render_template('500.html', details=send_to_html_json), 500

            else:
                result = result.get("Details")
                print('result ', result)
                print('rows returned: ', len(result))
                camera_list = []

                for camera in result:
                    camera_list.append({
                        "camera_make": camera[0],
                        "camera_ip_address": camera[1],
                        "camera_username": camera[2],
                        'camera_password': camera[3],
                        'camera_rtsp_address': camera[4],
                        'camera_region_of_interest': camera[5],
                        'camera_associated_services': camera[6],
                        "camera_id": camera[7]
                    })
                send_to_html_json = {
                    'camera_list': camera_list,
                    'logged_in_user': jwt_details.get("logged_in_user_name"),
                    'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                    'message': 'Please click on the Edit button to edit the camera settings.',
                    'page_title': 'Edit Camera'
                }
                print("details: ", send_to_html_json)
                session_values_json_redis.update({"ticket_status": "list_camera"})
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))

                return render_template('camera_list.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in list_camera of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administrator has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


# Edit Camera Details
@app.route("/edit_camera_details", methods=['GET', 'POST'])
@jwt_required()
def edit_camera_details():
    print("In edit_camera_details: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

        # POST
        if request.method == 'POST':
            form = request.form
            print("form: ", form)

            if form.get("submit_form"):
                print('update camera details')
                camera_make = form.get('camera_make')
                camera_make = camera_make.split(" - ")[1]
                camera_ip_address = form.get('camera_ip_address')
                camera_ip_address = camera_ip_address.split(" - ")[1]
                camera_username = form.get('camera_username')
                camera_username = camera_username.split(" - ")[1]
                camera_password = form.get('camera_password')
                camera_password = camera_password.split(" - ")[1]
                camera_rtsp_address = form.get('camera_rtsp_address')
                camera_rtsp_address = camera_rtsp_address.split(" - ")[1]
                camera_id = form.get('camera_id')
                result = sqlCommands.update_camera_record(camera_id, camera_make, camera_ip_address, camera_username, camera_password)
                if not result or result.get('Status') == "Fail" or result.get("Update_Count") == 0:
                    session_values_json_redis.update(
                        {"message": "System was unable to insert a camera record. Please try again."})
                    session_values_json_redis.update({"ticket_status": "edit_camera_details"})
                    redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                    print("insert a camera record failed")
                    print("redis in view_stream on insert new camera fail: ", session_values_json_redis)
                    send_to_html_json = {
                        'message': "System was unable to insert a camera record. Please try again",
                        'page_title': "Error"
                    }
                    return render_template('500.html', details=send_to_html_json), 500
                else:
                    details = result.get('Details')
                    session_values_json_redis.update({"message": "Camera successfully updated in the database. Please click the Edit button to make changes."})
                    session_values_json_redis.update({"ticket_status": "edit_region_of_interest"})
                    redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                    print('redis in add_region_of_interest on edit_camera_details update success: ', session_values_json_redis)
                    return redirect(url_for('edit_region_of_interest'))

            elif form.get("continue"):
                print('no update. move on')
                session_values_json_redis.update({"message": "Please click the Edit button to make changes."})
                session_values_json_redis.update({"ticket_status": "edit_region_of_interest"})
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                print('redis in add_region_of_interest on edit_camera_details update success: ',
                      session_values_json_redis)
                return redirect(url_for('edit_region_of_interest'))

        # GET
        else:
            print('redis in edit_camera_details: ', session_values_json_redis)
            camera_to_edit = session_values_json_redis.get('camera_to_be_edited')
            send_to_html_json = {
                'camera_make': camera_to_edit[0].get("camera_make"),
                'camera_ip_address': camera_to_edit[0].get("camera_ip_address"),
                'camera_username': camera_to_edit[0].get("camera_username"),
                'camera_password': camera_to_edit[0].get("camera_password"),
                'camera_rtsp_address': camera_to_edit[0].get("camera_rtsp_address"),
                'camera_id': camera_to_edit[0].get("camera_id"),
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': "Please make your changes and click Save to continue",
                'page_title': "Edit Camera Settings"
            }
            return render_template('edit_camera_details.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in list_camera of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administrator has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


# Edit Camera Details
@app.route("/edit_region_of_interest", methods=['GET', 'POST'])
@jwt_required()
def edit_region_of_interest():
    print("In edit_region_of_interest: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

        # POST
        if request.method == 'POST':
            form = request.form
            print("form: ", form)

        # GET
        else:
            print('redis in edit_camera_details: ', session_values_json_redis)
            camera_to_edit = session_values_json_redis.get('camera_to_be_edited')
            send_to_html_json = {
                'camera_region_of_interest': camera_to_edit[0].get("camera_region_of_interest"),
                'camera_id': camera_to_edit[0].get("camera_id"),
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': "Please make your changes and click Save to continue",
                'page_title': "Edit Camera Settings"
            }
            return render_template('edit_region_of_interest.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in edit_region_of_interest of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administrator has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


@app.route("/report_home", methods=['GET', 'POST'])
@jwt_required()
def report_home():
    print("In report_home: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

        if request.method == 'POST':
            if request.form:
                form = request.form
                print('form: ', form)
                if form.get('report') == 'vehicle_report':
                    session_values_json_redis.update({"ticket_status": "vehicle_report"})
                    redisCommands.redis_conn.set(redis_parent_key,
                                                 json.dumps(session_values_json_redis))
                    print('redis in report home before redirecting to vehicle_report')
                    return redirect(url_for('home'))

                elif form.get('report') == 'person_report':
                    session_values_json_redis.update({"ticket_status": "person_report"})
                    redisCommands.redis_conn.set(redis_parent_key,
                                                 json.dumps(session_values_json_redis))
                    print('redis in report_home before redirecting to person_report')
                    return redirect(url_for('home'))

                elif form.get('report') == 'trip_report':
                    session_values_json_redis.update({"ticket_status": "trip_report"})
                    redisCommands.redis_conn.set(redis_parent_key,
                                                 json.dumps(session_values_json_redis))
                    print('redis in report_home before redirecting to trip_report')
                    return redirect(url_for('home'))
        # GET
        else:
            send_to_html_json = {
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': 'Please click on a report from the list below.',
                'page_title': 'Report Home'
            }
            return render_template('report_home.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in report_home of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administration has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500
