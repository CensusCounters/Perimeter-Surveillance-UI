import cv2
from flask import render_template, url_for, redirect, request, session, make_response, Response, jsonify
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
                        # redisCommands.redis_conn.delete(redis_parent_key)
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
                    #response = make_response(redirect(url_for('home')))
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
            camera_location_name = form.get('camera_location')
            camera_sub_location_name = form.get('camera_sub_location')
            print("camera_sub_location_name: ", camera_sub_location_name)
            camera_location_id = form.get('camera_sub_location').split(",")[0]
            camera_sub_location_name = form.get('camera_sub_location').split(",")[1]
            camera_make = form.get('camera_make')
            camera_ip_address = form.get('camera_ip')
            camera_username = form.get('camera_username')
            camera_password = form.get('camera_password')
            camera_rtsp_address = routeMethods.build_rtsp_address(camera_make, camera_ip_address, camera_username,
                                                                  camera_password)

            print("rtsp: ", camera_rtsp_address)
            session_values_json_redis.update({"camera_location_name": camera_location_name})
            session_values_json_redis.update({"camera_sub_location_name": camera_sub_location_name})
            session_values_json_redis.update({"camera_location_id": camera_location_id})
            session_values_json_redis.update({"camera_make": camera_make})
            session_values_json_redis.update({"camera_ip_address": camera_ip_address})
            session_values_json_redis.update({"camera_username": camera_username})
            session_values_json_redis.update({"camera_password": camera_password})
            session_values_json_redis.update({"camera_rtsp_address": camera_rtsp_address})
            camera_associated_services = app.config["ASSOCIATED_SERVICES"]
            session_values_json_redis.update({"camera_associated_services": camera_associated_services})
            session_values_json_redis.update({"ticket_status": "add_region_of_interest"})
            redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
            print("redis in add camera: ", session_values_json_redis)
            message = 'Loading video feed from the camera... '
            send_to_html_json = {
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': message,
                'page_title': "View Camera"
            }
            return render_template('view_camera.html', details=send_to_html_json)
        # GET
        else:
            message = 'Please provide the camera details in the form and click Submit.'
            send_to_html_json = {
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': message,
                'page_title': "Add a New Camera"
            }
            return render_template('add_camera_details.html', details=send_to_html_json)

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
            image_file_name = None
            if form.get('continue'):
                # get a frame from opencv and save it to the hard drive
                # save the image location in redis
                # use that image in the canvas
                if session_values_json_redis.get('camera_rtsp_address'):
                    camera_rtsp_address = session_values_json_redis.get('camera_rtsp_address')
                    image_file_name = session_values_json_redis.get(
                        'camera_location_name') + "-" + session_values_json_redis.get('camera_ip_address') + ".jpg"
                elif session_values_json_redis.get('camera_to_be_edited'):
                    camera_to_edit = session_values_json_redis.get('camera_to_be_edited')
                    camera_rtsp_address = camera_to_edit[0].get("camera_rtsp_address")
                    image_file_name = camera_to_edit[0].get(
                        'camera_location_name') + "-" + camera_to_edit[0].get('camera_ip_address') + ".jpg"

                print("rtsp: ", camera_rtsp_address)
                camera = cv2.VideoCapture(camera_rtsp_address, cv2.CAP_FFMPEG)
                # camera_frame_image_actual_path = os.path.sep.join([app.config['IMAGE_UPLOADS'], image_file_name])
                camera_frame_image_actual_path = os.path.sep.join(
                    [app.config['BASE_PATH'].rstrip('/'), app.config['IMAGE_PATH_FOR_HTML'], image_file_name])
                frame_count = 0
                success = True
                while success:
                    success, image = camera.read()
                    frame_count += 1
                    if frame_count == 25:
                        cv2.imwrite(camera_frame_image_actual_path, image)
                        break

                camera_frame_image_html_path = os.path.sep.join(
                    [app.config["IMAGE_PATH_FOR_HTML"], os.path.basename(camera_frame_image_actual_path)])
                print('actual path: ', camera_frame_image_actual_path)
                print('html path: ', camera_frame_image_html_path)
                if session_values_json_redis.get("ticket_status") == "add_region_of_interest":
                    session_values_json_redis.update({"camera_frame_image_actual_path": camera_frame_image_actual_path})
                    session_values_json_redis.update({"camera_frame_image_html_path": camera_frame_image_html_path})
                    session_values_json_redis.update({"ticket_status": "add_region_of_interest"})
                    redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                    print("redis in view camera: ", session_values_json_redis)
                    return redirect(url_for('add_region_of_interest'))
                elif session_values_json_redis.get('camera_to_be_edited'):
                    session_values_json_redis.get('camera_to_be_edited')[0].update(
                        {"camera_frame_image_actual_path": camera_frame_image_actual_path})
                    session_values_json_redis.get('camera_to_be_edited')[0].update(
                        {"camera_frame_image_html_path": camera_frame_image_html_path})
                    redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                    print("redis in view camera: ", session_values_json_redis)
                    return redirect(url_for('edit_region_of_interest'))

        # GET
        else:
            print("redis in view_camera get: ", session_values_json_redis)
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
                print("redis in add_region_of_interest on insert new camera fail: ", session_values_json_redis)
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
            image_html_path = session_values_json_redis.get('camera_frame_image_html_path')
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
                    {
                        "message": "System was unable to retrieve camera details for camera id: " + camera_id + ". Please try again."})
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
                    'camera_location_id': camera_details.get("location_id"),
                    'camera_location_name': camera_details.get("location_name"),
                    'camera_sub_location_name': camera_details.get("sub_location_name"),
                    'camera_make': camera_details.get("camera_make"),
                    'camera_ip_address': camera_details.get("camera_ip_address"),
                    'camera_username': camera_details.get("camera_username"),
                    'camera_password': camera_details.get("camera_password"),
                    'camera_rtsp_address': camera_details.get("camera_rtsp_address"),
                    'camera_region_of_interest': camera_details.get("camera_region_of_interest"),
                    'camera_associated_services': camera_details.get("camera_associated_services"),
                    'camera_id': camera_details.get("id"),
                    'camera_frame_image_actual_path': camera_details.get("camera_frame_image_actual_path")
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
                camera_list = []
                camera_list = result.get("Details")
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
            camera_location = form.get('camera_location')
            camera_sub_location = form.get('camera_sub_location')
            camera_location_id = camera_sub_location.split(",")[0]
            camera_location_name = camera_sub_location.split(",")[1]
            camera_make = form.get('camera_make')
            camera_ip_address = form.get('camera_ip_address')
            camera_username = form.get('camera_username')
            #camera_username = camera_username.split(" - ")[1]
            camera_password = form.get('camera_password')
            #camera_password = camera_password.split(" - ")[1]
            camera_rtsp_address = form.get('camera_rtsp_address')
            #camera_rtsp_address = camera_rtsp_address.split(" - ")[1]
            camera_id = form.get('camera_id')
            camera_to_edit = session_values_json_redis.get('camera_to_be_edited')
            camera_region_of_interest = camera_to_edit[0].get('camera_region_of_interest')
            camera_associated_services = camera_to_edit[0].get('camera_associated_services')
            camera_frame_image_actual_path = camera_to_edit[0].get('camera_frame_image_actual_path')
            camera_to_edit = [{
                'camera_location_name': camera_location_name,
                'camera_make': camera_make,
                'camera_ip_address': camera_ip_address,
                'camera_username': camera_username,
                'camera_password': camera_password,
                'camera_rtsp_address': camera_rtsp_address,
                'camera_location_id': camera_location_id,
                'camera_id': camera_id,
                'camera_region_of_interest': camera_region_of_interest,
                'camera_associated_services': camera_associated_services,
                'camera_frame_image_actual_path': camera_frame_image_actual_path
            }]
            session_values_json_redis.update({'camera_to_be_edited': camera_to_edit})
            session_values_json_redis.update({"message": "Loading video feed from the camera..."})
            session_values_json_redis.update({"ticket_status": "edit_camera_details"})
            redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
            print('redis in edit_camera_details after successful database update: ', session_values_json_redis)
            message = 'Loading video feed from the camera...'
            send_to_html_json = {
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': message,
                'page_title': "View Camera"
            }
            return render_template('view_camera.html', details=send_to_html_json)

            # return redirect(url_for('view_camera'))

        # GET
        else:
            print("redis before edit_camera_html: ", session_values_json_redis)
            camera_to_edit = session_values_json_redis.get('camera_to_be_edited')
            send_to_html_json = {
                'camera_location_name': camera_to_edit[0].get("camera_location_name"),
                'camera_sub_location_name': camera_to_edit[0].get("camera_sub_location_name"),
                'camera_make': camera_to_edit[0].get("camera_make"),
                'camera_ip_address': camera_to_edit[0].get("camera_ip_address"),
                'camera_username': camera_to_edit[0].get("camera_username"),
                'camera_password': camera_to_edit[0].get("camera_password"),
                'camera_rtsp_address': camera_to_edit[0].get("camera_rtsp_address"),
                'camera_id': camera_to_edit[0].get("camera_id"),
                'camera_location_id': camera_to_edit[0].get("camera_location_id"),
                'logged_in_user': jwt_details.get("logged_in_user_name"),
                'logged_in_user_type': jwt_details.get("logged_in_user_type"),
                'message': "Please make your changes and click Continue to proceed",
                'page_title': "Edit Camera Settings"
            }
            print("json before edit_camera_html: ", send_to_html_json)
            return render_template('edit_camera_details.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in edit_camera of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administrator has been notified. Use the link below to "
                       "continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


# Edit Region Of Interest
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
            if form.get('region_of_interest'):
                camera_region_of_interest = json.loads(form.get('region_of_interest'))
                print("camera new region_of_interest: ", camera_region_of_interest)
                session_values_json_redis.get('camera_to_be_edited')[0].update(
                    {"camera_region_of_interest": camera_region_of_interest})
                # session_values_json_redis.update({"camera_region_of_interest": camera_region_of_interest})

            if form.get('roi_type'):
                roi_type = form.get('roi_type')
                if roi_type == 'Include':
                    roi_type = 'True'
                else:
                    roi_type = 'False'
                print("roi_type: ", roi_type)
                # session_values_json_redis.update({"camera_roi_type": roi_type})
                session_values_json_redis.get('camera_to_be_edited')[0].update({"camera_roi_type": roi_type})
            redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
            print('redis in edit_camera_details before database update: ', session_values_json_redis)
            result = routeMethods.update_camera_record(session_values_json_redis.get('camera_to_be_edited'))

            if not result or result.get('Status') == "Fail" or result.get("Update_Count") == 0:
                session_values_json_redis.update({"message": "System was unable to update the camera record. Please "
                                                             "try again."})
                session_values_json_redis.update({"ticket_status": "edit_region_of_interest"})
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                print("redis in view_stream on insert new camera fail: ", session_values_json_redis)
                send_to_html_json = {
                    'message': "System was unable to insert a camera record. Please try again",
                    'page_title': "Error"
                }
                return render_template('500.html', details=send_to_html_json), 500

            else:
                session_values_json_redis.update({"message": "Camera successfully updated in the database"})
                session_values_json_redis.update({"ticket_status": "home"})
                redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
                print('redis in edit_camera_details after successful database update: ', session_values_json_redis)
                send_to_html_json = {
                    'message': "Camera successfully updated in the database. Press Continue to proceed.",
                    'page_title': "Success"
                }
                return render_template('success_page.html', details=send_to_html_json), 500

        # GET
        else:
            print('redis in edit_region_of_interest: ', session_values_json_redis)
            camera_to_edit = session_values_json_redis.get('camera_to_be_edited')
            camera_frame_image_actual_path = camera_to_edit[0].get('camera_frame_image_actual_path')
            camera_frame_image_html_path = camera_to_edit[0].get('camera_frame_image_html_path')
            # camera_frame_image_html_path = os.path.sep.join([app.config["IMAGE_PATH_FOR_HTML"], os.path.basename(camera_frame_image_actual_path)])
            send_to_html_json = {
                'camera_region_of_interest': camera_to_edit[0].get("camera_region_of_interest"),
                'camera_frame_image': camera_frame_image_html_path,
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
        print(exc_type, "Exception in edit_region_of_interest of", fname, "at line number", exc_tb.tb_lineno, ":",
              error)
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
                if form.get('report') == 'detection_report':
                    session_values_json_redis.update({"ticket_status": "detection_report"})
                    redisCommands.redis_conn.set(redis_parent_key,
                                                 json.dumps(session_values_json_redis))
                    print('redis in report home before redirecting to detection_report')
                    return redirect(url_for('detection_report'))

                elif form.get('report') == 'camera_status':
                    session_values_json_redis.update({"ticket_status": "get_camera_status"})
                    redisCommands.redis_conn.set(redis_parent_key,
                                                 json.dumps(session_values_json_redis))
                    print('redis in report_home before redirecting to get_camera_status')
                    return redirect(url_for('get_camera_status'))

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


@app.route("/detection_report", methods=['GET', 'POST'])
@jwt_required()
def detection_report():
    print("In detection report: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        user_name = jwt_details.get("logged_in_user_name")
        user_type = jwt_details.get("logged_in_user_type")
        start_date = None
        end_date = None
        camera_ip_address = None
        detection_category = None
        alert_status = None
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(jwt_details.get('logged_in_user_id')))
        if request.method == 'POST':
            form = request.form
            print("form: ", form)
            if form.get('start_date'):
                start_date = form.get('start_date')
            if form.get('end_date'):
                end_date = form.get('end_date')
            if form.get('camera_ip_address'):
                camera_ip_address = form.get('camera_ip_address')
            if form.get('detection_category'):
                detection_category = form.get('detection_category')

            result = sqlCommands.get_detections_by_date(start_date, end_date, camera_ip_address, detection_category)
            # print("********************************: ", result)
            if not result or result.get('Status') == "Fail":
                print("generate detection report failed")
                send_to_html_json = {
                    'message': "An unexpected error occurred while generating the detection report. "
                               "The administration has been notified. Use the link below to continue.",
                    'logged_in_user': user_name,
                    'logged_in_user_type': user_type,
                    'page_title': "Error"
                }
                session_values_json_redis.update(
                    {"message": "An unexpected error occurred while generating the detection report. Please try again."})
                session_values_json_redis.update({"ticket_status": "report_home"})
                redisCommands.redis_conn.set(jwt_details.get('logged_in_user_id'),
                                             json.dumps(session_values_json_redis))
                print('redis in detection report on generate report fail: ', session_values_json_redis)
                return render_template('report_home.html', details=send_to_html_json)
                # return redirect(url_for('report_home'))
            else:
                detection_list = result.get("Details")
                print(type(detection_list))
                camera_list = []
                detection_category_list = []
                '''
                if len(detection_list) > 0:
                    for detection in detection_list:
                        if not any(
                                camera.get("camera_ip_address") == detection.get("camera_ip_address")
                                for camera in camera_list
                        ):
                            camera_list.append({"camera_ip_address": detection.get("camera_ip_address")})
                        if not any(
                                category.get("detection_category") == detection.get("detection_category")
                                for category in detection_category_list
                        ):
                            detection_category_list.append({"detection_category": detection.get("detection_category")})
                '''
                send_to_html_json = {
                    'detection_report_list': detection_list,
                    #'detection_category_list': detection_category_list,
                    #'camera_list': camera_list,
                    'start_date': start_date,
                    'end_date': end_date,
                    'camera_ip_address': camera_ip_address,
                    'detection_category': detection_category,
                    'message': 'Following records were found for the selected filters. Use the filters to refresh the report.',
                    'logged_in_user': user_name,
                    'logged_in_user_type': user_type,
                    'page_title': 'Detection Report'
                }
                print('redis in detection report on generate report success: ', session_values_json_redis)
                return render_template('detection_report.html', details=send_to_html_json)
        # GET
        else:
            start_date = datetime.combine(datetime.now(), time.min)
            print(start_date)  # 2023-02-10 00:00:00
            end_date = datetime.combine(datetime.now(), time.max)
            print(end_date)  # 2023-02-10 00:00:00

            result = sqlCommands.get_detections_by_date(start_date, end_date, 'All', 'All')
            print("********************************: ", result)
            if not result or result.get('Status') == "Fail":
                print("generate detection report failed")
                send_to_html_json = {
                    'message': "An unexpected error occured while generating the detection report. The administration has been notified. Use the link below to continue.",
                    'logged_in_user': user_name,
                    'logged_in_user_type': user_type,
                    'page_title': "Error"
                }
                session_values_json_redis.update(
                    {
                        "message": "An unexpected error occurred while generating the detection report. Please try again."})
                session_values_json_redis.update({"ticket_status": "report_home"})
                redisCommands.redis_conn.set(jwt_details.get('logged_in_user_id'),
                                             json.dumps(session_values_json_redis))
                print('redis in detection report on generate report fail: ', session_values_json_redis)
                return render_template('report_home.html', details=send_to_html_json)
                # return redirect(url_for('report_home'))
            else:
                detection_list = result.get("Details")
                camera_list = []
                detection_category_list = []
                '''
                if len(detection_list) > 0:
                    for detection in detection_list:
                        if not any(
                                camera.get("camera_ip_address") == detection.get("camera_ip_address")
                                for camera in camera_list
                        ):
                            camera_list.append({"camera_ip_address": detection.get("camera_ip_address")})
                        if not any(
                                category.get("detection_category") == detection.get("detection_category")
                                for category in detection_category_list
                        ):
                            detection_category_list.append({"detection_category": detection.get("detection_category")})
                '''
                send_to_html_json = {
                    'detection_report_list': detection_list,
                    #'detection_category_list': detection_category_list,
                    #'camera_list': camera_list,
                    'start_date': start_date,
                    'end_date': end_date,
                    'camera_ip_address': 'All',
                    'detection_category': 'All',
                    'message': 'Following records were found for the selected filters. '
                               'Use the filters to refresh the report.',
                    'logged_in_user': user_name,
                    'logged_in_user_type': user_type,
                    'page_title': 'Detection Report'
                }
                print('redis in detection report on generate report success: ', session_values_json_redis)
                return render_template('detection_report.html', details=send_to_html_json)


    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in detection_report of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administration has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        # print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


@app.route("/download_report", methods=['POST'])
@jwt_required()
def download_report():
    print("In download report: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        print("token: ", jwt_details)
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(jwt_details.get('logged_in_user_id')))

        if request.method == 'POST':
            if request.form:
                form = request.form
                print("form: ", form)
                start_date = datetime.strptime(form.get('start_date').split('.')[0], '%Y-%m-%d %H:%M:%S')
                print(start_date)
                end_date = datetime.strptime(form.get('end_date').split('.')[0], '%Y-%m-%d %H:%M:%S')
                print(end_date)

                report = session_values_json_redis.get('vehicle_report')
                csv_name = app.config["SAVED_REPORTS"] + 'vehicle_report_' + str(
                    start_date.strftime('%Y-%m-%d')) + "_" + str(end_date.strftime('%Y-%m-%d')) + ".csv"

                df = pd.DataFrame(report)
                df.to_csv(csv_name)
                return redirect(url_for('detection_report'))

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in download_report of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administration has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


@app.route("/start_display", methods=['GET', 'POST'])
@jwt_required()
def start_display():
    print("In start_display: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        user_name = jwt_details.get("logged_in_user_name")
        user_type = jwt_details.get("logged_in_user_type")
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(jwt_details.get('logged_in_user_id')))
        camera_rtsp_address = None
        camera_ip_address = None
        if request.method == 'POST':
            form = request.form
            print("form: ", form)
            if form.get('camera_rtsp_address'):
                camera_rtsp_address = form.get('camera_rtsp_address').split(" - ")[0]
                camera_ip_address = form.get('camera_rtsp_address').split(" - ")[1].replace(" ","")
                print("rtsp: ", camera_rtsp_address)
                session_values_json_redis.update({"rtsp_for_display": camera_rtsp_address})
                redisCommands.redis_conn.set(jwt_details.get('logged_in_user_id'),
                                             json.dumps(session_values_json_redis))
                print('redis in start display: ', session_values_json_redis)

            result = sqlCommands.get_rtsp_streams()
            print("result: ", result)
            if not result or result.get('Status') == "Fail" or len(result) == 0:
                print("get rtsp stream query failed")
                send_to_html_json = {
                    'message': "An unexpected error occured while retrieving rtsp streams. Please use the link below to continue.",
                    'logged_in_user': user_name,
                    'logged_in_user_type': user_type,
                    'page_title': "Error"
                }
                session_values_json_redis.update(
                    {"message": "An unexpected error occurred while retrieving rtsp streams. Please try again."})
                session_values_json_redis.update({"ticket_status": "start_display"})
                redisCommands.redis_conn.set(jwt_details.get('logged_in_user_id'),
                                             json.dumps(session_values_json_redis))
                print('redis in live streaming rtsp query fail: ', session_values_json_redis)
                return render_template('report_home.html', details=send_to_html_json)
            else:
                rtsp_list = result.get("Details")

                send_to_html_json = {
                    'rtsp_list': rtsp_list,
                    'selected_rtsp': camera_ip_address,
                    'message': 'Please select a camera to see live feed from it.',
                    'logged_in_user': user_name,
                    'logged_in_user_type': user_type,
                    'page_title': 'Live Feeds'
                }
                print('send_to_html_json in detection report on generate report success: ', send_to_html_json)
                return render_template('start_display.html', details=send_to_html_json)
        #GET
        else:
            result = sqlCommands.get_rtsp_streams()
            print("********************************: ", result)
            if not result or result.get('Status') == "Fail" or len(result) == 0:
                print("get rtsp stream query failed in GET")
                send_to_html_json = {
                    'message': "An unexpected error occured while retrieving rtsp streams. Please use the link below to continue.",
                    'logged_in_user': user_name,
                    'logged_in_user_type': user_type,
                    'page_title': "Error"
                }
                session_values_json_redis.update(
                    {"message": "An unexpected error occurred while retrieving rtsp streams. Please try again."})
                session_values_json_redis.update({"ticket_status": "start_display"})
                redisCommands.redis_conn.set(jwt_details.get('logged_in_user_id'),
                                             json.dumps(session_values_json_redis))
                print('redis in live streaming rtsp query fail: ', session_values_json_redis)
                return render_template('report_home.html', details=send_to_html_json)
            else:
                rtsp_list = result.get("Details")

                if session_values_json_redis.get("rtsp_for_display") is None:
                    camera_rtsp_address = app.config["TILED_RTSP"]
                    print("rtsp: ", camera_rtsp_address)
                    session_values_json_redis.update({"rtsp_for_display": camera_rtsp_address})
                    redisCommands.redis_conn.set(jwt_details.get('logged_in_user_id'),
                                                 json.dumps(session_values_json_redis))
                send_to_html_json = {
                    'rtsp_list': rtsp_list,
                    'message': 'Please select a camera to see live feed from it.',
                    'logged_in_user': user_name,
                    'logged_in_user_type': user_type,
                    'page_title': 'Live Feeds'
                }
                print('redis in start display on generate report success: ', session_values_json_redis)
                return render_template('start_display.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in start_display of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administration has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        # print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500

@app.route("/live_streaming", methods=['GET', 'POST'])
@jwt_required()
def live_streaming():
    print("In live streaming: ", request.method)
    jwt_details = get_jwt_identity()
    camera_rtsp_address = None
    session_values_json_redis = json.loads(redisCommands.redis_conn.get(jwt_details.get('logged_in_user_id')))

    try:
        if session_values_json_redis.get('rtsp_for_display'):
            camera_rtsp_address = session_values_json_redis.get('rtsp_for_display')
        print("rtsp: ", camera_rtsp_address)
        camera = cv2.VideoCapture(camera_rtsp_address, cv2.CAP_FFMPEG)
        return Response(routeMethods.generate_frames(camera),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in live_streaming of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administration has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        # print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


@app.route("/get_camera_status", methods=['GET','POST'])
@jwt_required()
def get_camera_status():
    print("In get camera status: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        user_name = jwt_details.get("logged_in_user_name")
        user_type = jwt_details.get("logged_in_user_type")
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(jwt_details.get('logged_in_user_id')))
        #POST
        if request.method == 'POST':
            form = request.form
            print("form: ", form)
            session_values_json_redis.update({"rtsp_for_display:":form.get("rtsp_address")})
            return redirect(url_for('start_display'))
        #GET
        else:

            result = sqlCommands.get_rtsp_streams()
            print("********************************: ", result)
            if not result or result.get('Status') == "Fail" or len(result) == 0:
                print("get rtsp stream query failed")
                send_to_html_json = {
                    'message': "An unexpected error occurred while retrieving rtsp streams. Please use the link below to "
                               "continue.",
                    'logged_in_user': user_name,
                    'logged_in_user_type': user_type,
                    'page_title': "Error"
                }
                session_values_json_redis.update(
                    {"message": "An unexpected error occurred while retrieving rtsp streams. Please try again."})
                session_values_json_redis.update({"ticket_status": "get_camera_status"})
                redisCommands.redis_conn.set(jwt_details.get('logged_in_user_id'),
                                             json.dumps(session_values_json_redis))
                print('redis in live streaming rtsp query fail: ', session_values_json_redis)
                return render_template('500.html', details=send_to_html_json)

            else:
                camera_list = result.get("Details")
                list_index = 0
                if len(camera_list) > 0:
                    for camera in camera_list:
                        print("index: ", list_index)
                        camera_frame_image_actual_path = camera.get("camera_frame_image_actual_path")
                        camera_frame_image_html_path = os.path.sep.join(
                            [app.config["IMAGE_PATH_FOR_HTML"], os.path.basename(camera_frame_image_actual_path)])
                        camera.update({"camera_frame_image_html_path": camera_frame_image_html_path})

                        #camera_ip_address = camera.get("camera_ip_address")
                        #ping_response = os.system("ping -c 1 " + camera_ip_address)
                        #print("ping response: ", ping_response)
                        #if ping_response == 0:
                        if list_index % 2 == 0:
                            camera.update({"camera_status": "Active"})
                        else:
                            camera.update({"camera_status": "Not Active"})
                        list_index += 1


                print("camera_list")

                send_to_html_json = {
                    'camera_list': camera_list,
                    'message': "Please click on the cards to see live streaming from the camera.",
                    'logged_in_user': user_name,
                    'logged_in_user_type': user_type,
                    'page_title': "Camera Activity Status"
                }
                session_values_json_redis.update({"ticket_status": "get_camera_status"})
                redisCommands.redis_conn.set(jwt_details.get('logged_in_user_id'),
                                             json.dumps(session_values_json_redis))
                print('redis in get_camera_status: ', session_values_json_redis)
                return render_template('camera_status.html', details=send_to_html_json)

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in live_streaming of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administration has been notified. Use the link below to "
                       "continue.",
            'page_title': "Error"
        }
        # print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


# Get Camera IP Addresses and Locations
@app.route("/get_camera_ip_address_list", methods=['GET'])
@jwt_required()
def get_camera_ip_address_list():
    print("In get_camera_ip_address_list: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

        result = sqlCommands.get_camera_ip_address_list()
        if not result or result.get('Status') == "Fail" or len(result.get("Details")) == 0:
            session_values_json_redis.update(
                {"message": "System was unable to retrieve the camera ip address list. Please try again."})
            session_values_json_redis.update({"ticket_status": "detection_report"})
            redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
            print("get location list failed")
            print("redis in add_camera on list location fail: ", session_values_json_redis)
            send_to_html_json = {
                'message': "System was unable to retrieve the location list. Please try again",
                'page_title': "Error"
            }
            return render_template('500.html', details=send_to_html_json), 500

        else:
            result = result.get("Details")
            print('result ', result)
            print('rows returned: ', len(result))
            #camera_ip_list = []
            #for camera in result:
            #    camera_ip_list.append({
            #        "location_name": location[0],
            #        "location_id": location[1]
            #    })
            return result

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in get_camera_ip_address_list of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administrator has been notified. "
                       "Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


# Get Camera IP Addresses and Locations
@app.route("/get_detection_category_list", methods=['GET'])
@jwt_required()
def get_detection_category_list():
    print("In get_detection_category_list: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

        result = sqlCommands.get_detection_category_list()
        if not result or result.get('Status') == "Fail" or len(result.get("Details")) == 0:
            session_values_json_redis.update(
                {"message": "System was unable to retrieve the detection category list. Please try again."})
            session_values_json_redis.update({"ticket_status": "detection_report"})
            redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
            print("get detection category list failed")
            print("redis in get detection category list fail: ", session_values_json_redis)
            send_to_html_json = {
                'message': "System was unable to retrieve the detection category list. Please try again",
                'page_title': "Error"
            }
            return render_template('500.html', details=send_to_html_json), 500

        else:
            result = result.get("Details")
            print('result ', result)
            print('rows returned: ', len(result))
            # camera_ip_list = []
            # for camera in result:
            #    camera_ip_list.append({
            #        "location_name": location[0],
            #        "location_id": location[1]
            #    })
            return result

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in get_detection_category_list of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administratior has been notified. "
                       "Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


# Get Camera IP Addresses and Locations
@app.route("/get_location_list", methods=['GET'])
@jwt_required()
def get_location_list():
    print("In get_location_list: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))
        source = request.args.get('source')
        need = request.args.get('need')
        print("ajax_data: ", source)
        print("ajax_data: ", need)

        result = sqlCommands.get_location_list()

        if not result or result.get('Status') == "Fail" or len(result.get("Locations")) == 0:
            session_values_json_redis.update(
                {"message": "System was unable to retrieve the location list. Please try again."})
            session_values_json_redis.update({"ticket_status": source})
            redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
            print("get location list failed")
            print("redis in get_location_list failed: ", session_values_json_redis)
            send_to_html_json = {
                'message': "System was unable to retrieve the location list. Please try again",
                'page_title': "Error"
            }
            return render_template('500.html', details=send_to_html_json), 500

        else:
            location_list = result.get("Locations")
            print('locations ', location_list)
            return location_list

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in get_location_list of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administrator has been notified. "
                       "Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500


# Get Camera IP Addresses and Locations
@app.route("/get_sub_location_list", methods=['GET'])
@jwt_required()
def get_sub_location_list():
    print("In get_sub_location_list: ", request.method)
    try:
        jwt_details = get_jwt_identity()
        redis_parent_key = jwt_details.get('redis_parent_key')
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))
        source = request.args.get('source')
        need = request.args.get('need')
        location = request.args.get('location')

        print("ajax_data: ", source)
        print("ajax_data: ", need)
        print("ajax_data: ", location)

        result = sqlCommands.get_sub_location_list(location)

        if not result or result.get('Status') == "Fail" or len(result.get("Sub_Locations")) == 0:
            session_values_json_redis.update(
                {"message": "System was unable to retrieve the sub location list. Please try again."})
            session_values_json_redis.update({"ticket_status": source})
            redisCommands.redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
            print("get location list failed")
            print("redis in get_location_list failed: ", session_values_json_redis)
            send_to_html_json = {
                'message': "System was unable to retrieve the sub location list. Please try again",
                'page_title': "Error"
            }
            return render_template('500.html', details=send_to_html_json), 500

        else:
            sub_location_list = result.get("Sub_Locations")
            print('sub locations ', sub_location_list)
            return sub_location_list

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in get_sub_location_list of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has happened. The administrator has been notified. "
                       "Use the link below to continue.",
            'page_title': "Error"
        }
        print("custom_exception: ", send_to_html_json)
        return render_template('500.html', details=send_to_html_json), 500

