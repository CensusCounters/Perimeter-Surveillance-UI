import json
from flask import render_template, redirect, url_for

def get_handler(jwt_details):
    redis_parent_key = jwt_details.get('redis_parent_key')
    send_to_html_json = {
        'logged_in_user': jwt_details.get("logged_in_user_name"),
        'logged_in_user_type': jwt_details.get("logged_in_user_type"),
        'message': 'Please click on a report from the list below.',
        'page_title': 'Report Home'
    }
    return render_template('report_home.html', details=send_to_html_json)


def post_handler(jwt_details, redis_conn, form):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    print('form: ', form)
    if form.get('report') == 'detection_report':
        #session_values_json_redis.update({"ticket_status": "detection_report"})
        redis_conn.set(redis_parent_key,
                                        json.dumps(session_values_json_redis))
        print('redis in report home before redirecting to detection_report')
        return redirect(url_for('detection_report'))

    elif form.get('report') == 'camera_status':
        #session_values_json_redis.update({"ticket_status": "get_camera_status"})
        redis_conn.set(redis_parent_key,
                                        json.dumps(session_values_json_redis))
        print('redis in report_home before redirecting to get_camera_status')
        return redirect(url_for('get_camera_status'))

    elif form.get('report') == 'alert_report':
        #session_values_json_redis.update({"ticket_status": "alert_report"})
        redis_conn.set(redis_parent_key,
                                        json.dumps(session_values_json_redis))
        print('redis in report_home before redirecting to alert_report')
        return redirect(url_for('alert_report'))