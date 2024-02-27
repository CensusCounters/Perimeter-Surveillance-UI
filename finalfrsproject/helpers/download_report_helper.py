import json
import datetime
from flask import app, redirect, url_for
import pandas as pd

def get_handler():
    return None

def post_handler(jwt_details,redis_conn, form):
    session_values_json_redis = json.loads(redis_conn.get(jwt_details.get('logged_in_user_id')))
    print("form: ", form)
    start_date = datetime.strptime(form.get('start_date').split('.')[0], '%Y-%m-%d %H:%M:%S')
    print(start_date)
    end_date = datetime.strptime(form.get('end_date').split('.')[0], '%Y-%m-%d %H:%M:%S')
    print(end_date)

    report = session_values_json_redis.get('vehicle_report')
    csv_name = app.config["SAVED_REPORTS"] + 'vehicle_report_' + str(
        start_date.strftime('%Y-%m-%d')) + "_" + str(end_date.strftime('%Y-%m-%d')) + ".csv"

    df = pd.DataFrame(report)
    df.to_csv(csv_name)
    return redirect(url_for('detection_report'))
