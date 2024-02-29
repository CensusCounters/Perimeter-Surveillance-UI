import json
from flask import render_template

def get_handler(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    print("redis parent key: ", redis_parent_key)
    #1platform_ui
    #1platform_ui
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

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

def post_handler(jwt_details, redis_conn, form):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    print("form: ", form)
    camera_location_name = form.get('camera_location')
    camera_sub_location = form.get('camera_sub_location')
    camera_location_id = camera_sub_location.split(",")[0]
    camera_sub_location_name = camera_sub_location.split(",")[1]
    camera_make = form.get('camera_make')
    camera_ip_address = form.get('camera_ip_address')
    camera_username = form.get('camera_username')
    camera_password = form.get('camera_password')
    camera_rtsp_address = form.get('camera_rtsp_address')
    camera_id = form.get('camera_id')
    camera_to_edit = session_values_json_redis.get('camera_to_be_edited')
    camera_region_of_interest = camera_to_edit[0].get('camera_region_of_interest')
    camera_associated_services = camera_to_edit[0].get('camera_associated_services')
    camera_frame_image_actual_path = camera_to_edit[0].get('camera_frame_image_actual_path')
    camera_to_edit = [{
        'camera_location_name': camera_location_name,
        'camera_sub_location_name': camera_sub_location_name,
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
    redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
    print('redis in edit_camera_details after successful database update: ', session_values_json_redis)
    message = 'Loading video feed from the camera...'
    send_to_html_json = {
        'logged_in_user': jwt_details.get("logged_in_user_name"),
        'logged_in_user_type': jwt_details.get("logged_in_user_type"),
        'message': message,
        'page_title': "View Camera"
    }
    return render_template('view_camera.html', details=send_to_html_json)