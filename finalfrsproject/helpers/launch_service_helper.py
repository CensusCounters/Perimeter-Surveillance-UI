import json
from finalfrsproject import sqlCommands, app
from flask import render_template, redirect, url_for, jsonify
import yaml
import re

# Function to generate sensor entry
def generate_sensor_entry(camera, index):
    return {
        f"sensor{index}": {
            "enable": 1,
            "type": "Camera",
            "id": camera["ip_address"],
            "location": "45.293701447;-75.8303914499;48.1557479338",
            "description": camera["rtsp"],
            "coordinate": "5.2;10.1;11.2"
        }
    }

# Function to generate place entry
def generate_place_entry(camera, index):
    return {
        f"place{index}": {
            "enable": 1,
            "id": index,
            "type": camera["location"],
            "name": camera["sub_location"],
            "location": "30.32;-40.55;100.0",
            "coordinate": "1.0;2.0;3.0",
            "place-sub-field1": "192.168.1.172",
            "place-sub-field2": "empty2",
            "place-sub-field3": "empty3"
        }
    }

def generate_analytics_entries(camera, start_index=1):
    analytics_entries = {}
    associated_services = json.loads(camera["associated_services"])
    for i, service in enumerate(associated_services, start=start_index):
        analytics_entries[f"analytics{i}"] = {
            "enable": 1,
            "id": i,
            "description": service,
            "source": "IP camera",
            "version": 1.0
        }
    print("Whats happening--- ")
    return analytics_entries, start_index + len(associated_services)


def generate_config_yaml(data, output_file_path):
    if not data:
        return "No data available to generate YAML file."
    
    combined_yaml = {}
    analytics_index = 1

    for index, camera in enumerate(data):
        combined_yaml.update(generate_sensor_entry(camera, index))
        combined_yaml.update(generate_place_entry(camera, index))
        analytics_entries, analytics_index = generate_analytics_entries(camera, analytics_index)
        combined_yaml.update(analytics_entries)

    # Convert to YAML
    yaml_output = yaml.dump(combined_yaml, sort_keys=False, allow_unicode=True)

    pattern = re.compile(r'(?m)^((sensor|place|analytics)\d+:)')
    yaml_output = pattern.sub(r'\n\1', yaml_output)


    with open(output_file_path, 'w') as file:
        file.write(yaml_output)

    return f"YAML file generated successfully at: {output_file_path}"

def generate_new_yaml_file(data, output_file_path):
    if not data:
        return "No data available to generate YAML file."
    
    # transformed_data = []
    
    # for item in data:
    #     roi_dict = json.loads(item['roi'])
    #     roi_object = roi_dict['objects'][0]
        
    #     transformed_item = {
    #         'id': int(item['id']),
    #         'source': item['rtsp'],
    #         'enable_roi': True,
    #         'roi': {
    #             'top': roi_object['top'],
    #             'left': roi_object['left'],
    #             'bottum': roi_object['top'] + roi_object['height'],
    #             'right': roi_object['left'] + roi_object['width'],
    #         }
    #     }

    #     transformed_data.append(transformed_item)
    # Transform data
    transformed_data = []
    for item in sorted(data, key=lambda x: int(x['id'])):
        roi_dict = json.loads(item['roi'])
        
        # Process all ROI objects
        roi_objects_list = []
        for roi_object in roi_dict['objects']:
            roi_details = {
                'top': roi_object['top'],
                'left': roi_object['left'],
                'bottum': roi_object['top'] + roi_object['height'],  
                'right': roi_object['left'] + roi_object['width'],  
            }
            roi_objects_list.append(roi_details)

        transformed_item = {
            'id': int(item['id']),
            'source': item['rtsp'],
            'enable_roi': True,
            'roi': roi_objects_list  # Assign the list of processed ROI objects
        }

        transformed_data.append(transformed_item)

    batch_size_str = f"batch_size: {len(transformed_data)}\n"
    yaml_data = yaml.dump(transformed_data, allow_unicode=True, sort_keys=False)

    final_yaml = batch_size_str + yaml_data

    with open(output_file_path, 'w') as file:
        file.write(final_yaml)

    return f"YAML file generated successfully at: {output_file_path}"

def handle_post_request(jwt_details, redis_conn, form):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    
    select_list = form.getlist('select_list[]')
    # select_list = [json.loads(html.unescape(item)) for item in select_list]
    # print("select_list: ", select_list)

    parsed_items = []

    # Iterate over each item, parse it as JSON, and append to the parsed_items list
    for item in select_list:
        try:
            parsed_json = json.loads(item)
            parsed_items.append(parsed_json)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return jsonify({'message': "Error when handling data."}), 500

    print("parsed items: ", parsed_items)
    output_file_path = app.config["BASE_PATH"] +'/main_config.yaml'
    output_file_path_new = app.config["BASE_PATH"] +'/msgconv_config.yaml'

    result_status = generate_new_yaml_file(parsed_items, output_file_path)

    result_status = generate_config_yaml(parsed_items, output_file_path_new)

    return jsonify({'message': result_status}), 200


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
        # print("details: ", send_to_html_json)
        session_values_json_redis.update({"ticket_status": "list_camera"})
        redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))

        return render_template('launch_service.html', details=send_to_html_json)