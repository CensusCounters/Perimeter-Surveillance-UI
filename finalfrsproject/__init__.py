from flask import Flask
#from reports_blueprint import reports_blueprint
import os
#import redis
#from flask_session import Session
from flask_jwt_extended import JWTManager
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)

app.config["IMAGE_UPLOADS"] = "/home/manish/Documents/Platform-UI/Platform-UI-v1/finalfrsproject/static/images/uploads"
app.config["IMAGE_PATH_FOR_HTML"] = "/static/images/uploads"
app.config["SAVED_REPORTS"] = "/home/manish/Documents/ImageCapture/Final-FRS-Project-v3/finalfrsproject/reports/"
ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
#app.config["POSTGRESQL_URL"] = "census-postgres_db"
app.config["POSTGRESQL_URL"] = "172.17.0.1"

app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=10)
app.config['SECRET_KEY'] = 'ed83ade6b7ed34ff7ed0042759170f72'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['WTF_CSRF_ENABLED'] = False

jwt = JWTManager(app)
csrf = CSRFProtect()
csrf.init_app(app)

try:
    if not os.path.exists(app.config["IMAGE_UPLOADS"]):
        os.makedirs(app.config["IMAGE_UPLOADS"])
    else:
        print(f"Found upload directory")    
except OSError:
        print(f"ERROR: creating directory upload directory")


try:
    if not os.path.exists(app.config["SAVED_REPORTS"]):
        os.makedirs(app.config["SAVED_REPORTS"])
    else:
        print(f"Found directory for saved reports")    
except OSError:
   print(f"ERROR: creating directory for saved reports]")

from finalfrsproject import routes

