import datetime, os, sys
import json

from flask import jsonify
from finalfrsproject import app
import pandas as pd
from datetime import datetime

def post_handler(request):
    try:
        json_payload = request.json
        start_date = json_payload.get('start_date')
        print(start_date)
        start_date = datetime.strptime(start_date.split('.')[0], '%Y-%m-%d %H:%M:%S')
        end_date = json_payload.get('end_date')
        end_date = datetime.strptime(end_date.split('.')[0], '%Y-%m-%d %H:%M:%S')
        print(end_date)
        report = list(json_payload.get('report'))
        print(type(report))

        #csv_name = app.config["SAVED_REPORTS"] + 'detection_report_' + str(
        #    start_date.strftime('%Y-%m-%d')) + "_" + str(end_date.strftime('%Y-%m-%d')) + ".csv"

        csv_name= os.path.sep.join([app.config['BASE_PATH'],app.config["SAVED_REPORTS"]]) + 'detection_report_' + str(
            start_date.strftime('%Y-%m-%d')) + "_" + str(end_date.strftime('%Y-%m-%d')) + ".csv"
        print("csv_name: ", csv_name)

        df = pd.DataFrame(report)
        df.to_csv(csv_name)
        send_to_html_json = {
                'message': "Report saved at " + csv_name +".",
                'page_title': "Success"
        }
        return jsonify(send_to_html_json), 200

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, "Exception in download_report of", fname, "at line number", exc_tb.tb_lineno, ":", error)
        send_to_html_json = {
            'message': "An unexpected error has occurred. "
                       " The administration has been notified. Use the link below to continue.",
            'page_title': "Error"
        }
        return jsonify(send_to_html_json), 500