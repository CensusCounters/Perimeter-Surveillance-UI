import json
from flask import render_template
from finalfrsproject import sqlCommands, app

def get_handler(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    user_name = jwt_details.get("logged_in_user_name")
    user_type = jwt_details.get("logged_in_user_type")
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))
    if session_values_json_redis.get("rtsp_for_display") is None:
        camera_rtsp_address = app.config["TILED_RTSP"]
        print("rtsp: ", camera_rtsp_address)
        session_values_json_redis.update({"rtsp_for_display": camera_rtsp_address})
        redis_conn.set(jwt_details.get('logged_in_user_id'),
                                        json.dumps(session_values_json_redis))
        send_to_html_json = {
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
    camera_id = None
    print("form: ", form)
    if form.get('camera_identifier'):
        camera_identifier = form.get('camera_identifier')
        if camera_identifier != 'TILED':
            camera_id = camera_identifier.split("---")[0]
            camera_rtsp_address = camera_identifier.split("---")[1]
            camera_identifier = camera_id + "---" + camera_rtsp_address
        else:
            camera_rtsp_address = app.config["TILED_RTSP"]

        print("rtsp: ", camera_identifier)
        session_values_json_redis.update({"rtsp_for_display": camera_rtsp_address})
        redis_conn.set(jwt_details.get('logged_in_user_id'),
                                        json.dumps(session_values_json_redis))
        print('redis in start display: ', session_values_json_redis)

    send_to_html_json = {
        'camera_identifier': camera_identifier,
        'message': 'Please select a camera to see live feed from it.',
        'logged_in_user': user_name,
        'logged_in_user_type': user_type,
        'page_title': 'Live Feeds'
    }
    print('send_to_html_json in detection report on generate report success: ', send_to_html_json)
    return render_template('start_display.html', details=send_to_html_json)
