# camera_helpers.py

import json
from flask import render_template

def process_form_request(request, redis_conn, redis_parent_key):
    """Process POST request and update session values."""
    form = request.form
    session_values = {}
    session_values = json.loads(redis_conn.get(redis_parent_key) or '{}')

    print("session_values:::: - ", session_values)
    if form.get('region_of_interest'):
        camera_region_of_interest = json.loads(form.get('region_of_interest'))
        session_values["camera_region_of_interest"] = camera_region_of_interest

    if form.get('roi_type'):
        roi_type = 'True' if form.get('roi_type') == 'Include' else 'False'
        session_values["camera_roi_type"] = roi_type

    return session_values

def update_session_redis(redis_conn, redis_parent_key, updates):
    """Fetch, update, and save session values to Redis."""
    print("redis_conn.get(redis_parent_key) - ", redis_conn.get(redis_parent_key))
    session_values_json = json.loads(redis_conn.get(redis_parent_key) or '{}')
    print("session_values_json:::::::: ", session_values_json)
    session_values_json.update(updates)
    redis_conn.set(redis_parent_key, json.dumps(session_values_json))
    return session_values_json

def insert_camera_record(routeMethods, session_values):
    """Insert new camera record to the database."""
    result = routeMethods.insert_new_camera_record(session_values)
    return result

def handle_database_response(redis_conn, redis_parent_key, result):
    """Handle database operation result and update session accordingly."""
    if not result or result.get('Status') == "Fail" or result.get("Insert_Count") == 0:
        message = "System was unable to insert a camera record. Please try again."
        ticket_status = "add_camera"
        error = True
    else:
        message = "New camera successfully added to the database."
        ticket_status = "home"
        error = False
    
    updates = {
        "message": message,
        "ticket_status": ticket_status
    }
    update_session_redis(redis_conn, redis_parent_key, updates)
    return message, error

def add_region_intrest_get(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))
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