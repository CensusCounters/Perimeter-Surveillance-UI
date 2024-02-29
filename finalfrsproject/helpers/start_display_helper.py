import json
from flask import render_template
from finalfrsproject import sqlCommands, app

def get_handler(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    user_name = jwt_details.get("logged_in_user_name")
    user_type = jwt_details.get("logged_in_user_type")
    print(redis_conn.get(redis_parent_key))
    print(user_name)
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))
    camera_rtsp_address = None
    camera_ip_address = None
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
        redis_conn.set(jwt_details.get('logged_in_user_id'),
                                        json.dumps(session_values_json_redis))
        print('redis in live streaming rtsp query fail: ', session_values_json_redis)
        return render_template('report_home.html', details=send_to_html_json)
    else:
        rtsp_list = result.get("Details")

        if session_values_json_redis.get("rtsp_for_display") is None:
            camera_rtsp_address = app.config["TILED_RTSP"]
            print("rtsp: ", camera_rtsp_address)
            session_values_json_redis.update({"rtsp_for_display": camera_rtsp_address})
            redis_conn.set(jwt_details.get('logged_in_user_id'),
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


def post_handler(jwt_details, redis_conn, form):
    redis_parent_key = jwt_details.get('redis_parent_key')
    user_name = jwt_details.get("logged_in_user_name")
    user_type = jwt_details.get("logged_in_user_type")
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))
    camera_rtsp_address = None
    camera_ip_address = None
    print("form: ", form)
    if form.get('camera_rtsp_address'):
        camera_rtsp_address = form.get('camera_rtsp_address').split(" - ")[0]
        camera_ip_address = form.get('camera_rtsp_address').split(" - ")[1].replace(" ","")
        print("rtsp: ", camera_rtsp_address)
        session_values_json_redis.update({"rtsp_for_display": camera_rtsp_address})
        redis_conn.set(jwt_details.get('logged_in_user_id'),
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
        redis_conn.set(jwt_details.get('logged_in_user_id'),
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
