import json, os
from finalfrsproject import app, sqlCommands
from flask import redirect, url_for, render_template

def get_handler(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    user_name = jwt_details.get("logged_in_user_name")
    user_type = jwt_details.get("logged_in_user_type")
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    result = sqlCommands.get_rtsp_streams()
    print("********************************: ", result)
    if not result or result.get('Status') == "Fail" or len(result) == 0:
        print("get rtsp stream query failed")
        send_to_html_json = {
            'message': "An unexpected error occurred while retrieving rtsp streams. "
                       "Please use the link below to continue.",
            'logged_in_user': user_name,
            'logged_in_user_type': user_type,
            'page_title': "Error"
        }
        session_values_json_redis.update(
            {"message": "An unexpected error occurred while retrieving rtsp streams. Please try again."})
        session_values_json_redis.update({"ticket_status": "get_camera_status"})
        redis_conn.set(jwt_details.get('logged_in_user_id'),
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
        redis_conn.set(jwt_details.get('logged_in_user_id'),
                                        json.dumps(session_values_json_redis))
        print('redis in get_camera_status: ', session_values_json_redis)
        return render_template('camera_status.html', details=send_to_html_json)


def post_handler(jwt_details, redis_conn, form):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))
    print("form: ", form)
    session_values_json_redis.update({"rtsp_for_display:":form.get("rtsp_address")})
    redis_conn.set(jwt_details.get('redis_parent_key'), json.dumps(session_values_json_redis))
    return redirect(url_for('start_display'))