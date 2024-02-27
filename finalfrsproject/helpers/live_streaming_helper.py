import json
import cv2
from flask import Response
from finalfrsproject import routeMethods

def get_handler():
    return None

def post_handler(jwt_details, redis_conn):
    camera_rtsp_address = None
    session_values_json_redis = json.loads(redis_conn.get(jwt_details.get('logged_in_user_id')))
    if session_values_json_redis.get('rtsp_for_display'):
        camera_rtsp_address = session_values_json_redis.get('rtsp_for_display')
        print("rtsp: ", camera_rtsp_address)
        camera = cv2.VideoCapture(camera_rtsp_address, cv2.CAP_FFMPEG)
        return Response(routeMethods.generate_frames(camera),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
