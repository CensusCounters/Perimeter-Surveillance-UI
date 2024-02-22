import cv2
from finalfrsproject import app, sqlCommands, jwt
import json

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

def build_rtsp_address(camera_make, camera_ip_address, camera_username, camera_password):
	if camera_make == 'HikVision':
		# rtsp: // username:password@< address >: < port > / Streaming / Channels / < id >
		camera_rtsp_address = "rtsp://" + camera_username + ":" + camera_password + "@" + camera_ip_address + ":554/Streaming/Channels/101"
	elif camera_make == 'Prama':
		camera_rtsp_address = "rtsp://" + camera_username + ":" + camera_password + "@" + camera_ip_address + ":554/Streaming/Channels/101"
	elif camera_make == 'Dahua':
		# rtsp://<username>:<password>@<ip>:<port>/cam/realmonitor?channel=<channelNo>&subtype=<typeNo>
		camera_rtsp_address = "rtsp://" + camera_username + ":" + camera_password + "@" + camera_ip_address + ":554/cam/realMonitor?channel=1&subtype=1"
	elif camera_make == "CPPlus":
		# rtsp://< user >: < pass >@< cameraip >: < port > / cam / realmonitor?channel = 1 & subtype = 0
		camera_rtsp_address = "rtsp://" + camera_username + ":" + camera_password + "@" + camera_ip_address + ":554/cam/realMonitor?channel=1&subtype=1"
	else:
		camera_rtsp_address = "rtsp://ec2-13-235-48-204.ap-south-1.compute.amazonaws.com:8554/stream1"
	# camera_rtsp = "rtsp://rtspstream:26d9ae61eaffdb00d6acc9f30e03ad3f@zephyr.rtsp.stream/pattern"
	return camera_rtsp_address


def insert_new_camera_record(session_values_json_redis):
	print("in routesMethod.insert_new_camera_record")
	camera_location_id = session_values_json_redis.get("camera_location_id")
	camera_make = session_values_json_redis.get("camera_make")
	camera_ip_address = session_values_json_redis.get("camera_ip_address")
	camera_username = session_values_json_redis.get("camera_username")
	camera_password = session_values_json_redis.get("camera_password")
	camera_rtsp_address = session_values_json_redis.get("camera_rtsp_address")
	camera_region_of_interest = json.dumps(session_values_json_redis.get("camera_region_of_interest"))
	camera_associated_services = session_values_json_redis.get("camera_associated_services")
	logged_in_user_id = session_values_json_redis.get("logged_in_user_id")
	camera_roi_type = session_values_json_redis.get("camera_roi_type")
	camera_frame_image_actual_path = session_values_json_redis.get("camera_frame_image_actual_path")

	result = sqlCommands.insert_new_camera_record(logged_in_user_id, camera_make, camera_ip_address, camera_username, camera_password, camera_rtsp_address,
				camera_region_of_interest, camera_associated_services, camera_roi_type, camera_location_id, camera_frame_image_actual_path)
	return result

def update_camera_record(camera_to_edit):
	print("in routesMethod.update_camera_record: ", camera_to_edit)
	camera_id = camera_to_edit[0].get("camera_id")
	camera_location_id = camera_to_edit[0].get("camera_location_id")
	camera_make = camera_to_edit[0].get("camera_make")
	camera_ip_address = camera_to_edit[0].get("camera_ip_address")
	camera_username = camera_to_edit[0].get("camera_username")
	camera_password = camera_to_edit[0].get("camera_password")
	camera_rtsp_address = camera_to_edit[0].get("camera_rtsp_address")
	camera_region_of_interest = json.dumps(camera_to_edit[0].get("camera_region_of_interest"))
	camera_associated_services = camera_to_edit[0].get("camera_associated_services")
	logged_in_user_id = camera_to_edit[0].get("logged_in_user_id")
	camera_roi_type = camera_to_edit[0].get("camera_roi_type")
	camera_frame_image_actual_path = camera_to_edit[0].get("camera_frame_image_actual_path")

	result = sqlCommands.update_camera_record(camera_id, camera_make, camera_ip_address, camera_username, camera_password, camera_rtsp_address,
				camera_region_of_interest, camera_associated_services, camera_roi_type, camera_location_id, camera_frame_image_actual_path)
	return result
