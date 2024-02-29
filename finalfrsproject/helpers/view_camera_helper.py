import cv2
import os
import json
from flask import url_for, redirect, Response

def get_camera_rtsp_address(session_values_json_redis):
    camera_rtsp_address = None
    if session_values_json_redis.get('camera_rtsp_address'):
        camera_rtsp_address = session_values_json_redis.get('camera_rtsp_address')
    elif session_values_json_redis.get('camera_to_be_edited'):
        camera_to_edit = session_values_json_redis.get('camera_to_be_edited')
        camera_rtsp_address = camera_to_edit[0].get("camera_rtsp_address")
    return camera_rtsp_address

def save_camera_frame(camera_rtsp_address, session_values_json_redis, app_config):
    image_file_name = get_image_file_name(session_values_json_redis)
    camera = cv2.VideoCapture(camera_rtsp_address, cv2.CAP_FFMPEG)
    camera_frame_image_actual_path = os.path.sep.join(
        [app_config['BASE_PATH'].rstrip('/'), app_config['IMAGE_PATH_FOR_HTML'].lstrip('/'), image_file_name])
    print("base_path: ", [app_config['BASE_PATH'].rstrip('/')])
    print("html_path: ", app_config['IMAGE_PATH_FOR_HTML'])
    print(camera_frame_image_actual_path)
    frame_count = 0
    success = True
    while success:
        success, image = camera.read()
        frame_count += 1
        if frame_count == 25:
            cv2.imwrite(camera_frame_image_actual_path, image)
            break
    camera_frame_image_html_path = os.path.sep.join(
        [app_config["IMAGE_PATH_FOR_HTML"], os.path.basename(camera_frame_image_actual_path)])
    return camera_frame_image_actual_path, camera_frame_image_html_path

def get_image_file_name(session_values_json_redis):
    if session_values_json_redis.get('camera_location_name') and session_values_json_redis.get('camera_ip_address'):
        return f"{session_values_json_redis.get('camera_location_name')}-{session_values_json_redis.get('camera_ip_address')}.jpg"
    return "default.jpg"

def update_session_values(session_values_json_redis, paths, redis_conn, redis_parent_key):
    actual_path, html_path = paths
    if session_values_json_redis.get("ticket_status") == "add_region_of_interest":
        session_values_json_redis.update({"camera_frame_image_actual_path": actual_path, "camera_frame_image_html_path": html_path, "ticket_status": "add_region_of_interest"})
    elif session_values_json_redis.get('camera_to_be_edited'):
        session_values_json_redis.get('camera_to_be_edited')[0].update({"camera_frame_image_actual_path": actual_path, "camera_frame_image_html_path": html_path})
    redis_conn.set(redis_parent_key, json.dumps(session_values_json_redis))

def redirect_based_on_ticket_status(session_values_json_redis):
    if session_values_json_redis.get("ticket_status") == "add_region_of_interest":
        return redirect(url_for('add_region_of_interest'))
    elif session_values_json_redis.get('camera_to_be_edited'):
        return redirect(url_for('edit_region_of_interest'))
    
def generate_frames(camera):
    while True:
        success, frame = camera.read()  # Read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # Concatenate frame one by one and show result

def stream_camera(camera_rtsp_address):
    camera = cv2.VideoCapture(camera_rtsp_address, cv2.CAP_FFMPEG)
    return Response(generate_frames(camera), mimetype='multipart/x-mixed-replace; boundary=frame')