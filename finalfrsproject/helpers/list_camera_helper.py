import json
from finalfrsproject import sqlCommands
from flask import render_template, redirect, url_for

def handle_post_request(jwt_details, redis_conn, form):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    print("form: ", form)
    camera_id = form.get("camera_id")
    result = sqlCommands.get_camera_details(camera_id)

    if not result or result.get('Status') == "Fail" or len(result.get("Details")) == 0:
        #session_values_json_redis.update({"message": "System was unable to retrieve camera details for camera id: " + camera_id + ". Please try again."})
        #session_values_json_redis.update({"ticket_status": "list_camera"})
        #redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
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
        redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
        return redirect(url_for('edit_camera_details'))


def handle_get_request(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    result = sqlCommands.get_camera_list()

    if not result or result.get('Status') == "Fail":
        session_values_json_redis.update(
            {"message": "System was unable to retrieve the camera list. Please try again."})
        session_values_json_redis.update({"ticket_status": "home"})
        redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
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
            'message': 'Please click anywhere on the row to edit the camera settings.',
            'page_title': 'Edit Camera'
        }
        print("details: ", send_to_html_json)
        session_values_json_redis.update({"ticket_status": "list_camera"})
        redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))

        return render_template('camera_list.html', details=send_to_html_json)