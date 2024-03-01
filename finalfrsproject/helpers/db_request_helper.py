import json
from flask import render_template, jsonify
from finalfrsproject import sqlCommands


def camera_ip_address_list(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    result = sqlCommands.get_camera_ip_address_list()
    if not result or result.get('Status') == "Fail" or len(result.get("Details")) == 0:
        #session_values_json_redis.update(
        #    {"message": "System was unable to retrieve the camera ip address list. Please try again."})
        #session_values_json_redis.update({"ticket_status": "detection_report"})
        #redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
        print("get location list failed")
        #print("redis in add_camera on list location fail: ", session_values_json_redis)
        send_to_html_json = {
            'message': "System was unable to retrieve the camera list. Please try again.",
            'page_title': "Error"
        }
        #return render_template('500.html', details=send_to_html_json), 500
        return jsonify(send_to_html_json), 500
    else:
        result = result.get("Details")
        print('result ', result)
        print('rows returned: ', len(result))
        return result


def detection_category_list(jwt_details, redis_conn):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    result = sqlCommands.get_detection_category_list()
    if not result or result.get('Status') == "Fail" or len(result.get("Details")) == 0:
        #session_values_json_redis.update(
        #    {"message": "System was unable to retrieve the detection category list. Please try again."})
        #session_values_json_redis.update({"ticket_status": "detection_report"})
        #redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
        print("get detection category list failed")
        #print("redis in get detection category list fail: ", session_values_json_redis)
        send_to_html_json = {
            'message': "System was unable to retrieve the detection category list. Please try again",
            'page_title': "Error"
        }
        #return render_template('500.html', details=send_to_html_json), 500
        return jsonify(send_to_html_json), 500
    else:
        result = result.get("Details")
        print('result ', result)
        print('rows returned: ', len(result))
        return result
    
def location_list(jwt_details, redis_conn, request):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))
    source = request.args.get('source')
    need = request.args.get('need')
    print("ajax_data: ", source)
    print("ajax_data: ", need)

    result = sqlCommands.get_location_list()

    if not result or result.get('Status') == "Fail" or len(result.get("Locations")) == 0:
        #session_values_json_redis.update(
        #    {"message": "System was unable to retrieve the location list. Please try again."})
        #session_values_json_redis.update({"ticket_status": source})
        #redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
        print("get location list failed")
        #print("redis in get_location_list failed: ", session_values_json_redis)
        send_to_html_json = {
            'message': "System was unable to retrieve the location list. Please try again",
            'page_title': "Error"
        }
        #return render_template('500.html', details=send_to_html_json), 500
        return jsonify(send_to_html_json), 500
    else:
        location_list = result.get("Locations")
        print('locations ', location_list)
        return location_list
    
def sub_location_list(jwt_details, redis_conn, request):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))
    source = request.args.get('source')
    need = request.args.get('need')
    location = request.args.get('location')

    print("ajax_data: ", source)
    print("ajax_data: ", need)
    print("ajax_data: ", location)

    result = sqlCommands.get_sub_location_list(location)

    if not result or result.get('Status') == "Fail" or len(result.get("Sub_Locations")) == 0:
        #session_values_json_redis.update(
        #    {"message": "System was unable to retrieve the sub location list. Please try again."})
        #session_values_json_redis.update({"ticket_status": source})
        #redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))
        print("get location list failed")
        #print("redis in get_location_list failed: ", session_values_json_redis)
        send_to_html_json = {
            'message': "System was unable to retrieve the sub location list. Please try again",
            'page_title': "Error"
        }
        #return render_template('500.html', details=send_to_html_json), 500
        return jsonify(send_to_html_json), 500

    else:
        sub_location_list = result.get("Sub_Locations")
        print('sub locations ', sub_location_list)
        return sub_location_list