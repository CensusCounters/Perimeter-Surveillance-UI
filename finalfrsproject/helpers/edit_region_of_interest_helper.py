import json
from flask import render_template
from finalfrsproject import routeMethods

def get_handler(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

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

def post_handler(jwt_details, redis_conn, form):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

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
    redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
    print('redis in edit_camera_details before database update: ', session_values_json_redis)
    result = routeMethods.update_camera_record(session_values_json_redis.get('camera_to_be_edited'))

    if not result or result.get('Status') == "Fail" or result.get("Update_Count") == 0:
        session_values_json_redis.update({"message": "System was unable to update the camera record. Please "
                                                        "try again."})
        session_values_json_redis.update({"ticket_status": "edit_region_of_interest"})
        redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
        print("redis in view_stream on insert new camera fail: ", session_values_json_redis)
        send_to_html_json = {
            'message': "System was unable to insert a camera record. Please try again",
            'page_title': "Error"
        }
        return render_template('500.html', details=send_to_html_json), 500

    else:
        session_values_json_redis.update({"message": "Camera successfully updated in the database"})
        session_values_json_redis.update({"ticket_status": "home"})
        redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
        print('redis in edit_camera_details after successful database update: ', session_values_json_redis)
        send_to_html_json = {
            'message': "Camera successfully updated in the database. Press Continue to proceed.",
            'page_title': "Success"
        }
        return render_template('success_page.html', details=send_to_html_json), 200