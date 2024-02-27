import json
from flask import render_template
import datetime, time
from finalfrsproject import sqlCommands, redisCommands

def get_handler(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    user_name = jwt_details.get("logged_in_user_name")
    user_type = jwt_details.get("logged_in_user_type")
    start_date = None
    end_date = None
    camera_ip_address = None
    detection_category = None
    alert_status = None
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    start_date = datetime.combine(datetime.now(), time.min)
    print(start_date)  # 2023-02-10 00:00:00
    end_date = datetime.combine(datetime.now(), time.max)
    print(end_date)  # 2023-02-10 00:00:00

    result = sqlCommands.get_detections_by_date(start_date, end_date, 'All', 'All')
    print("********************************: ", result)
    if not result or result.get('Status') == "Fail":
        print("generate detection report failed")
        send_to_html_json = {
            'message': "An unexpected error occured while generating the detection report. The administration has been notified. Use the link below to continue.",
            'logged_in_user': user_name,
            'logged_in_user_type': user_type,
            'page_title': "Error"
        }
        session_values_json_redis.update(
            {
                "message": "An unexpected error occurred while generating the detection report. Please try again."})
        session_values_json_redis.update({"ticket_status": "report_home"})
        redisCommands.redis_conn.set(jwt_details.get('logged_in_user_id'),
                                        json.dumps(session_values_json_redis))
        print('redis in detection report on generate report fail: ', session_values_json_redis)
        return render_template('report_home.html', details=send_to_html_json)
        # return redirect(url_for('report_home'))
    else:
        detection_list = result.get("Details")
        camera_list = []
        detection_category_list = []
        '''
        if len(detection_list) > 0:
            for detection in detection_list:
                if not any(
                        camera.get("camera_ip_address") == detection.get("camera_ip_address")
                        for camera in camera_list
                ):
                    camera_list.append({"camera_ip_address": detection.get("camera_ip_address")})
                if not any(
                        category.get("detection_category") == detection.get("detection_category")
                        for category in detection_category_list
                ):
                    detection_category_list.append({"detection_category": detection.get("detection_category")})
        '''
        send_to_html_json = {
            'detection_report_list': detection_list,
            #'detection_category_list': detection_category_list,
            #'camera_list': camera_list,
            'start_date': start_date,
            'end_date': end_date,
            'camera_ip_address': 'All',
            'detection_category': 'All',
            'message': 'Following records were found for the selected filters. '
                        'Use the filters to refresh the report.',
            'logged_in_user': user_name,
            'logged_in_user_type': user_type,
            'page_title': 'Detection Report'
        }
        print('redis in detection report on generate report success: ', session_values_json_redis)
        return render_template('detection_report.html', details=send_to_html_json)


def post_handler(jwt_details, redis_conn, form):
    redis_parent_key = jwt_details.get('redis_parent_key')
    user_name = jwt_details.get("logged_in_user_name")
    user_type = jwt_details.get("logged_in_user_type")
    start_date = None
    end_date = None
    camera_ip_address = None
    detection_category = None
    alert_status = None
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    print("form: ", form)
    if form.get('start_date'):
        start_date = form.get('start_date')
    if form.get('end_date'):
        end_date = form.get('end_date')
    if form.get('camera_ip_address'):
        camera_ip_address = form.get('camera_ip_address')
    if form.get('detection_category'):
        detection_category = form.get('detection_category')

    result = sqlCommands.get_detections_by_date(start_date, end_date, camera_ip_address, detection_category)
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
        session_values_json_redis.update(
            {"message": "An unexpected error occurred while generating the detection report. Please try again."})
        session_values_json_redis.update({"ticket_status": "report_home"})
        redis_conn.set(jwt_details.get('logged_in_user_id'),
                                        json.dumps(session_values_json_redis))
        print('redis in detection report on generate report fail: ', session_values_json_redis)
        return render_template('report_home.html', details=send_to_html_json)
        # return redirect(url_for('report_home'))
    else:
        detection_list = result.get("Details")
        print(type(detection_list))
        camera_list = []
        detection_category_list = []
        '''
        if len(detection_list) > 0:
            for detection in detection_list:
                if not any(
                        camera.get("camera_ip_address") == detection.get("camera_ip_address")
                        for camera in camera_list
                ):
                    camera_list.append({"camera_ip_address": detection.get("camera_ip_address")})
                if not any(
                        category.get("detection_category") == detection.get("detection_category")
                        for category in detection_category_list
                ):
                    detection_category_list.append({"detection_category": detection.get("detection_category")})
        '''
        send_to_html_json = {
            'detection_report_list': detection_list,
            #'detection_category_list': detection_category_list,
            #'camera_list': camera_list,
            'start_date': start_date,
            'end_date': end_date,
            'camera_ip_address': camera_ip_address,
            'detection_category': detection_category,
            'message': 'Following records were found for the selected filters. Use the filters to refresh the report.',
            'logged_in_user': user_name,
            'logged_in_user_type': user_type,
            'page_title': 'Detection Report'
        }
        print('redis in detection report on generate report success: ', session_values_json_redis)
        return render_template('detection_report.html', details=send_to_html_json)
