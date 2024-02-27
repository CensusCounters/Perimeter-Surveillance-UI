import json
from ..routeMethods import build_rtsp_address

def process_post_request(form, jwt_details, redis_parent_key, redis_conn, app_config):
    """
    Process the POST request for adding a camera.
    """

    redis_parent_key = jwt_details.get('redis_parent_key')
    details = json.loads(redis_conn.get(redis_parent_key))

    print("details::::::", details)

    camera_location_name = form.get('camera_location')
    camera_sub_location_name = form.get('camera_sub_location').split(",")[1]
    camera_location_id = form.get('camera_sub_location').split(",")[0]
    camera_make = form.get('camera_make')
    camera_ip_address = form.get('camera_ip')
    camera_username = form.get('camera_username')
    camera_password = form.get('camera_password')
    camera_rtsp_address = build_rtsp_address(camera_make, camera_ip_address, camera_username, camera_password)

    session_values_json_redis = {
        "camera_location_name": camera_location_name,
        "camera_sub_location_name": camera_sub_location_name,
        "camera_location_id": camera_location_id,
        "camera_make": camera_make,
        "camera_ip_address": camera_ip_address,
        "camera_username": camera_username,
        "camera_password": camera_password,
        "camera_rtsp_address": camera_rtsp_address,
        "camera_associated_services": app_config["ASSOCIATED_SERVICES"],
        "ticket_status": "add_region_of_interest",
        "logged_in_user_id": details['logged_in_user_id']
    }

    # session_values_json_redis.update(details)

    redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))

    return {
        'logged_in_user': jwt_details.get("logged_in_user_name"),
        'logged_in_user_type': jwt_details.get("logged_in_user_type"),
        'message': 'Loading video feed from the camera...',
        'page_title': "View Camera"
    }

def get_initial_details(jwt_details):
    """
    Prepare the initial details for rendering the add camera template on a GET request.
    """
    return {
        'logged_in_user': jwt_details.get("logged_in_user_name"),
        'logged_in_user_type': jwt_details.get("logged_in_user_type"),
        'message': 'Please provide the camera details in the form and click Submit.',
        'page_title': "Add a New Camera"
    }
