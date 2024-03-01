import json
from datetime import datetime, timedelta
from flask import render_template, url_for, redirect, request, session, make_response, Response, jsonify
from finalfrsproject import app, ALLOWED_PHOTO_EXTENSIONS, sqlCommands, jwt, routeMethods, redisCommands
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt, jwt_required, set_access_cookies, \
    unset_jwt_cookies

# Helper methods
from .helpers.auth_helper import fetch_user_details, get_redis_session, login_response, error_response, delete_session_from_redis, logout_get, logout_post
from .helpers.home_helper import process_home_form, get_home_details
from .helpers.add_camera_helper import process_post_request, get_initial_details
from .helpers.view_camera_helper import (get_camera_rtsp_address, save_camera_frame, update_session_values,
                                 redirect_based_on_ticket_status, stream_camera)
from .helpers.add_region_of_interest import process_form_request, add_region_intrest_get, insert_camera_record, handle_database_response
from .helpers import list_camera_helper as list_camera_helper
from .helpers import edit_camera_details_helper as edit_camera_handler
from .helpers import edit_region_of_interest_helper as edit_region_interest_helper
from .helpers import report_home_helper as report_home_helper
from .helpers import detection_report_helper as detection_report_helper
from .helpers import download_report_helper as download_report_helper
from .helpers import start_display_helper as start_display_helper
from .helpers import live_streaming_helper as live_streaming_helper
from .helpers import get_camera_status_helper as get_camera_status_helper
from .helpers import db_request_helper as db_request_helper
from .helpers import alert_report_helper as alert_report_helper

# Kafka 
import threading
#from .kafka_consumer import start_kafka_consumer
#threading.Thread(target=start_kafka_consumer).start()

# Define the custom filter
def json_truncate(value, length=20):
    json_str = json.dumps(value)
    print("json_str: ", json_str)
    if not json_str or json_str == 'null':
        print("json_str: is null")
        return "None"
    else:
        return json_str[:length] + '...' if len(json_str) > length else json_str

# Register the custom filter with Jinja2
app.jinja_env.filters['json_truncate'] = json_truncate

#     # Logout
@app.route("/", methods=['GET'])
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return error_response("Login", "Welcome. Please login with your name and password to continue.")
    
    # POST request
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return error_response("Login", "No username and password provided.")

    user_details = fetch_user_details(username, password)
    if not user_details or user_details.get('Status') == "Fail" or not user_details.get("Details"):
        return error_response("Login", "Login information incorrect. Please check the username and password entered.")

    session_data = get_redis_session(user_details["Details"][2], "platform_ui")
    destination = session_data.get("ticket_status", "home")

    return login_response(user_details["Details"], destination)

@app.route("/logout", methods=['GET', 'POST'])
@jwt_required()
def logout():
    print("In Logout: ", request.method)
    jwt_details = get_jwt_identity()
    # GET
    if request.method == 'GET':
        return logout_get(jwt_details)
    # POST
    else:
        return logout_post(jwt_details, request, unset_jwt_cookies)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


# handle-alert
@app.route('/handle-alert', methods=['POST'])
@jwt_required()
def handle_alert():
    if request.method == 'POST':
        # Extract alert_id from the posted JSON data
        data = request.get_json()
        alert_id = data.get('alert_id')

        # Process the alert_id as needed
        print(f'Received alert_id: {alert_id}')
        jwt_details = get_jwt_identity()
        logged_in_user_id = jwt_details.get('logged_in_user_id')

        sqlCommands.update_alert_detection(alert_id, logged_in_user_id)

        # Respond back to the AJAX call
        return jsonify({"message": "Alert ID received successfully"})


@app.route("/home", methods=['GET', 'POST'])
@jwt_required()
def home():
    jwt_details = get_jwt_identity()
    redis_parent_key = jwt_details.get('redis_parent_key')

    if request.method == 'GET' or (request.method == 'POST' and not request.form):
            delete_session_from_redis(redis_parent_key)
            print('Session data cleared from Redis.')

    if request.method == 'POST':
        next_page = process_home_form(redis_parent_key, request.form, jwt_details)
        if next_page:
            return redirect(url_for(next_page))

    return render_template('home.html', details=get_home_details(jwt_details, request.method))


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


@app.route("/add_camera", methods=['GET', 'POST'])
@jwt_required()
def add_camera():
    print("In add_camera: ", request.method)
    jwt_details = get_jwt_identity()
    redis_parent_key = jwt_details.get('redis_parent_key')

    if request.method == 'GET':
        details = get_initial_details(jwt_details)
        return render_template('add_camera_details.html', details=details)
    else:
        form = request.form
        details = process_post_request(form, jwt_details, redis_parent_key, redisCommands.redis_conn, app.config)
        return render_template('view_camera.html', details=details)


@app.route("/view_camera", methods=['GET', 'POST'])
@jwt_required()
def view_camera():
    print("In view_camera: ", request.method)
    jwt_details = get_jwt_identity()
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

    camera_rtsp_address = get_camera_rtsp_address(session_values_json_redis)

    if request.method == 'GET':
        return stream_camera(camera_rtsp_address)

    else:
        paths = save_camera_frame(camera_rtsp_address, session_values_json_redis, app.config)
        update_session_values(session_values_json_redis, paths, redisCommands.redis_conn, redis_parent_key)
        return redirect_based_on_ticket_status(session_values_json_redis)


@app.route("/add_region_of_interest", methods=['GET', 'POST'])
@jwt_required()
def add_region_of_interest():
    jwt_details = get_jwt_identity()
    redis_parent_key = jwt_details.get('redis_parent_key')

    if request.method == 'GET':
        return add_region_intrest_get(jwt_details, redisCommands.redis_conn)
    else:
        session_values = process_form_request(request, redisCommands.redis_conn,redis_parent_key)
        result = insert_camera_record(routeMethods, session_values)
        message, error = handle_database_response(redisCommands.redis_conn, redis_parent_key, result)

        send_to_html_json = {'message': message, 'page_title': "Error" if error else "Success"}
        template = '500.html' if error else 'success_page.html'
        return render_template(template, details=send_to_html_json), 500 if error else 200


# List Cameras
@app.route("/list_camera", methods=['GET', 'POST'])
@jwt_required()
def list_camera():
    print("In list_camera: ", request.method)
    jwt_details = get_jwt_identity()
    # GET
    if request.method == 'GET':
        return list_camera_helper.handle_get_request(jwt_details, redisCommands.redis_conn)
    # POST
    else:
        return list_camera_helper.handle_post_request(jwt_details, redisCommands.redis_conn, request.form)


# Edit Camera Details
@app.route("/edit_camera_details", methods=['GET', 'POST'])
@jwt_required()
def edit_camera_details():
    print("In edit_camera_details: ", request.method)
    jwt_details = get_jwt_identity()
    # GET
    if request.method == 'GET':
        return edit_camera_handler.get_handler(jwt_details, redisCommands.redis_conn)
    # POST
    else:
        return edit_camera_handler.post_handler(jwt_details, redisCommands.redis_conn, request.form)


# Edit Region Of Interest
@app.route("/edit_region_of_interest", methods=['GET', 'POST'])
@jwt_required()
def edit_region_of_interest():
    print("In edit_region_of_interest: ", request.method)
    jwt_details = get_jwt_identity()
    # GET
    if request.method == 'GET':
        return edit_region_interest_helper.get_handler(jwt_details, redisCommands.redis_conn)
    # POST
    else:
        return edit_region_interest_helper.post_handler(jwt_details, redisCommands.redis_conn, request.form)


@app.route("/report_home", methods=['GET', 'POST'])
@jwt_required()
def report_home():
    print("In report_home: ", request.method)
    jwt_details = get_jwt_identity()
    # GET
    if request.method == 'GET':
        return report_home_helper.get_handler(jwt_details)
    # POST
    else:
        return report_home_helper.post_handler(jwt_details, redisCommands.redis_conn, request.form)
    

@app.route("/detection_report", methods=['GET', 'POST'])
@jwt_required()
def detection_report():
    print("In detection report: ", request.method)
    jwt_details = get_jwt_identity()
    # GET
    if request.method == 'GET':
        return detection_report_helper.get_handler(jwt_details, redisCommands.redis_conn)
    # POST
    else:
        return detection_report_helper.post_handler(jwt_details, redisCommands.redis_conn, request.form)
    

@app.route("/alert_report", methods=['GET', 'POST'])
@jwt_required()
def alert_report():
    print("In alert report: ", request.method)
    jwt_details = get_jwt_identity()
    # GET
    if request.method == 'GET':
        return alert_report_helper.get_handler(jwt_details, redisCommands.redis_conn)
    # POST
    else:
        return alert_report_helper.post_handler(jwt_details, redisCommands.redis_conn, request.form)
        

@app.route("/download_report", methods=['POST'])
@jwt_required()
def download_report():
    print("In download report: ", request.method)
    jwt_details = get_jwt_identity()
    print("token: ", jwt_details)
    # POST
    if request.method == 'POST':
        return download_report_helper.post_handler(request)


@app.route("/start_display", methods=['GET', 'POST'])
@jwt_required()
def start_display():
    print("In start_display: ", request.method)
    jwt_details = get_jwt_identity()
    # GET
    if request.method == 'GET':
        return start_display_helper.get_handler(jwt_details, redisCommands.redis_conn)
    # POST
    else:
        return start_display_helper.post_handler(jwt_details, redisCommands.redis_conn, request.form)
    

@app.route("/live_streaming", methods=['GET', 'POST'])
@jwt_required()
def live_streaming():
    print("In live streaming: ", request.method)
    jwt_details = get_jwt_identity()
    return live_streaming_helper.post_handler(jwt_details, redisCommands.redis_conn)


@app.route("/get_camera_status", methods=['GET','POST'])
@jwt_required()
def get_camera_status():
    print("In get camera status: ", request.method)
    jwt_details = get_jwt_identity()
    #GET
    if request.method == 'GET':
        return get_camera_status_helper.get_handler(jwt_details, redisCommands.redis_conn)
    #POST
    else:
        return get_camera_status_helper.post_handler(jwt_details, redisCommands.redis_conn, request.form)


# Get Camera IP Addresses and Locations
@app.route("/get_camera_ip_address_list", methods=['GET'])
@jwt_required()
def get_camera_ip_address_list():
    print("In get_camera_ip_address_list: ", request.method)
    jwt_details = get_jwt_identity()
    return db_request_helper.camera_ip_address_list(jwt_details, redisCommands.redis_conn)


# Get Camera IP Addresses and Locations
@app.route("/get_detection_category_list", methods=['GET'])
@jwt_required()
def get_detection_category_list():
    print("In get_detection_category_list: ", request.method)
    jwt_details = get_jwt_identity()
    return db_request_helper.detection_category_list(jwt_details, redisCommands.redis_conn)


# Get Camera IP Addresses and Locations
@app.route("/get_location_list", methods=['GET'])
@jwt_required()
def get_location_list():
    print("In get_location_list: ", request.method)
    jwt_details = get_jwt_identity()
    return db_request_helper.location_list(jwt_details, redisCommands.redis_conn, request)

# Get Camera IP Addresses and Locations
@app.route("/get_sub_location_list", methods=['GET'])
@jwt_required()
def get_sub_location_list():
    print("In get_sub_location_list: ", request.method)
    jwt_details = get_jwt_identity()
    return db_request_helper.sub_location_list(jwt_details, redisCommands.redis_conn, request)

@app.route("/start_display_alerts", methods=['GET','POST'])
@jwt_required()
def start_display_alerts():
    print("In display alerts: ", request.method)
    jwt_details = get_jwt_identity()
    #GET
    if request.method == 'GET':
        return render_template('display_alerts.html',details="")
    #POST
    else:
        return get_camera_status_helper.post_handler(jwt_details, redisCommands.redis_conn, request.form)
