from flask import Flask
import os
from flask_jwt_extended import JWTManager
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO

app = Flask(__name__)
#socketio = SocketIO(app)
socketio = SocketIO(app, async_mode='eventlet')

app.config["BASE_PATH"] = "/home/manish/Documents/Platform-UI/Platform-UI-v1/finalfrsproject"
app.config["IMAGE_PATH_FOR_HTML"] = "/static/images/uploads"
app.config["KNOWN_DETECTION_PATH_FOR_HTML"] = "/static/images/detections"
app.config["SAVED_REPORTS"] = "/static/reports/"
app.config["ASSOCIATED_SERVICES"] = ["MOG2", "People_Detection"]
app.config["TILED_RTSP"] = "rtsp://ec2-13-235-48-204.ap-south-1.compute.amazonaws.com:8554/stream1"
app.config["INACTIVE_RTSP_IMAGE"] = "/static/images/camera-not-available.jpg"

ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
#app.config["POSTGRESQL_URL"] = "census-postgres_db"
app.config["POSTGRESQL_URL"] = "172.17.0.1"

app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=10)
app.config['SECRET_KEY'] = 'ed83ade6b7ed34ff7ed0042759170f72'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['WTF_CSRF_ENABLED'] = True

jwt = JWTManager(app)
csrf = CSRFProtect()
csrf.init_app(app)

try:
    if not os.path.exists(os.path.sep.join([app.config['BASE_PATH'], app.config['IMAGE_PATH_FOR_HTML']])):
        os.makedirs(os.path.sep.join([app.config['BASE_PATH'], app.config['IMAGE_PATH_FOR_HTML']]))
    else:
        print(f"Found upload directory")    
except OSError:
        print(f"ERROR: creating directory upload directory")


try:
    if not os.path.exists(os.path.sep.join([app.config['BASE_PATH'],app.config['KNOWN_DETECTION_PATH_FOR_HTML']])):
        os.makedirs(os.path.sep.join([app.config['BASE_PATH'],app.config['KNOWN_DETECTION_PATH_FOR_HTML']]))
    else:
        print(f"Found detection directory")
except OSError:
        print(f"ERROR: creating directory detection directory")

try:
    if not os.path.exists(os.path.sep.join([app.config['BASE_PATH'],app.config["SAVED_REPORTS"]])):
        os.makedirs(os.path.sep.join([app.config['BASE_PATH'],app.config["SAVED_REPORTS"]]))
    else:
        print(f"Found directory for saved reports")    
except OSError:
   print(f"ERROR: creating directory for saved reports")

from finalfrsproject import routes, errors

