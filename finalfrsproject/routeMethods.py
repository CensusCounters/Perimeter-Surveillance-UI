import os, shutil
import cv2
from finalfrsproject import app, sqlCommands, jwt
import json
from flask import request
from werkzeug.utils import secure_filename
from datetime import datetime, timezone, timedelta

def allowed_file(filename, allowed_extensions):
	return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in allowed_extensions


def generate_frames(camera):
	while True:
		success, frame = camera.read()
		if not success:
			break
		else:
			ret, buffer = cv2.imencode('.jpg',frame)
			frame = buffer.tobytes()
			yield (b'--frame\r\n'
				   b'Content-Type:image/jpeg\r\n\r\n' + frame + b'\r\n') # concat frame one by one and show result


def insert_new_camera_record(session_values_json_redis):
	print("in routesMethod.insert_new_camera_record")
	camera_make = session_values_json_redis.get("camera_make")
	camera_ip_address = session_values_json_redis.get("camera_ip_address")
	camera_username = session_values_json_redis.get("camera_username")
	camera_password = session_values_json_redis.get("camera_password")
	camera_rtsp_address = session_values_json_redis.get("camera_rtsp_address")
	camera_region_of_interest = json.dumps(session_values_json_redis.get("camera_region_of_interest"))
	camera_associated_services = session_values_json_redis.get("camera_associated_services")
	logged_in_user_id = session_values_json_redis.get("logged_in_user_id")
	camera_roi_type = session_values_json_redis.get("camera_roi_type")

	result = sqlCommands.insert_new_camera_record(logged_in_user_id, camera_make, camera_ip_address, camera_username, camera_password, camera_rtsp_address, camera_region_of_interest, camera_associated_services, camera_roi_type)
	return result