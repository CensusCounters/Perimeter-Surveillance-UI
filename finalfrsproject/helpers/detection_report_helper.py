import json
from flask import render_template
from datetime import datetime, time
from finalfrsproject import sqlCommands, redisCommands

def parse_datestring(date_str):
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"time data '{date_str}' does not match expected formats")

def get_handler(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    print("redis_parent_key: ", redis_parent_key)
    user_name = jwt_details.get("logged_in_user_name")
    user_type = jwt_details.get("logged_in_user_type")
    start_date = None
    end_date = None
    camera_ip_address = None
    detection_category = None
    alert_status = None
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    date_time_now = sqlCommands.local_to_utc(datetime.now())
    start_date = datetime.combine(date_time_now, time.min)
    print(start_date)  # 2023-02-10 00:00:00
    end_date = datetime.combine(date_time_now, time.max)
    print(end_date)  # 2023-02-10 00:00:00

    result = sqlCommands.get_detections_by_date(start_date, end_date, None, None)
    print("********************************: ", result)
    if not result or result.get('Status') == "Fail":
        print("generate detection report failed")
        send_to_html_json = {
            'message': "An unexpected error occurred while generating the detection report. "
                       "The administration has been notified. Use the link below to continue.",
            'logged_in_user': user_name,
            'logged_in_user_type': user_type,
            'page_title': "Error"
        }
        #session_values_json_redis.update({"message": "An unexpected error occurred while generating the detection report. Please try again."})
        #session_values_json_redis.update({"ticket_status": "report_home"})
        redisCommands.redis_conn.set(jwt_details.get('redis_parent_key'),json.dumps(session_values_json_redis))
        print('redis in detection report on generate report fail: ', session_values_json_redis)
        return render_template('report_home.html', details=send_to_html_json)
        # return redirect(url_for('report_home'))
    else:
        detection_list = result.get("Details")
        send_to_html_json = {
            'detection_report_list': detection_list,
            'start_date': start_date,
            'end_date': end_date,
            'message': 'Following records were found for the selected filters. '
                        'Use the filters to refresh the report.',
            'logged_in_user': user_name,
            'logged_in_user_type': user_type,
            'page_title': 'Detection Report'
        }
        print(send_to_html_json)
        print('redis in detection report on generate report success: ', session_values_json_redis)
        return render_template('detection_report.html', details=send_to_html_json)


def post_handler(jwt_details, redis_conn, form):
    redis_parent_key = jwt_details.get('redis_parent_key')
    user_name = jwt_details.get("logged_in_user_name")
    user_type = jwt_details.get("logged_in_user_type")
    start_date = None
    end_date = None
    detection_category_id = None
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))
    camera_id = None

    print("form: ", form)
    if form.get('start_date'):
        start_date = form.get('start_date')
    if form.get('end_date'):
        end_date = form.get('end_date')
    if form.get('camera_identifier'):
        camera_id = form.get('camera_identifier')
        if camera_id == "":
            camera_id = None
    if form.get('detection_category'):
        detection_category_id = form.get('detection_category')
        if detection_category_id == "":
            detection_category_id = None

    # start_date_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S.%f')
    # end_date_dt = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S.%f')
    start_date_dt = parse_datestring(start_date)
    end_date_dt = parse_datestring(end_date)

    start_date_utc = sqlCommands.local_to_utc(start_date_dt)
    end_date_utc = sqlCommands.local_to_utc(end_date_dt)

    #result = sqlCommands.get_detections_by_date(start_date, end_date, camera_ip_address, location_name, sub_location_name, detection_category)
    result = sqlCommands.get_detections_by_date(start_date_utc, end_date_utc, camera_id, detection_category_id)
    # print("********************************: ", result)
    if not result or result.get('Status') == "Fail":
        print("generate detection report failed")
        send_to_html_json = {
            'message': "An unexpected error occurred while generating the detection report. "
                        "The administration has been notified. Use the link below to continue.",
            'logged_in_user': user_name,
            'logged_in_user_type': user_type,
            'page_title': "Error"
        }
        #session_values_json_redis.update(
        #    {"message": "An unexpected error occurred while generating the detection report. Please try again."})
        #session_values_json_redis.update({"ticket_status": "report_home"})
        #redis_conn.set(jwt_details.get('redis_parent_key'),
        #                                json.dumps(session_values_json_redis))
        #print('redis in detection report on generate report fail: ', session_values_json_redis)
        return render_template('report_home.html', details=send_to_html_json)
        # return redirect(url_for('report_home'))
    else:
        detection_list = result.get("Details")
        send_to_html_json = {
            'detection_report_list': detection_list,
            'start_date': start_date,
            'end_date': end_date,
            'camera_id': camera_id,
            'detection_category_id': detection_category_id,
            'message': 'Following records were found for the selected filters. Use the filters to refresh the report.',
            'logged_in_user': user_name,
            'logged_in_user_type': user_type,
            'page_title': 'Detection Report'
        }
        print(send_to_html_json)
        print('redis in detection report on generate report success: ', session_values_json_redis)
        return render_template('detection_report.html', details=send_to_html_json)
