from kafka import KafkaConsumer, errors
import json
# from finalfrsproject import socketio, sqlCommands
import time
import pathlib
from datetime import datetime

SENDING_PAUSE_TIME = 5 # mins
MAX_ALERTS_NUMBER = 10 # after that pause for SENDING_PAUSE_TIME
MIN_ALERTS_THRESHOLD = 2 # Alerts needed within MAX_ALERTS_INTERVAL to activate sending
MAX_ALERTS_INTERVAL = 10 # interval in seconds
TIMESTAMP_FORMAT='%Y-%m-%dT%H:%M:%S.%fZ'
TOPIC_NAME = 'events'

KAFKA_SERVERS='localhost:9092'

print(f"AlertSender is loaded and connected to topic '{TOPIC_NAME}'")

alerts_calculator = {}
last_sent_timestamp = {}
count_sent_messages = {}

def start_kafka_consumer():
    try:
        consumer = KafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=KAFKA_SERVERS,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id="99999",
        )
        
        for event in consumer:
            if event:
                print("#################### KAFKA BEGIN ####################")
                print(f"Received event: {event.value}")
                event_data = event.value
                camera_id = event_data['sensor']['id']
                message_timestamp = datetime.strptime(event_data['@timestamp'], TIMESTAMP_FORMAT)
                print(f"Message consumed from camera {camera_id} with timestamp {event_data['@timestamp']}")

                if camera_id in alerts_calculator.keys():
                    alerts_calculator[camera_id] = [x for x in alerts_calculator[camera_id] if (message_timestamp - x).total_seconds() <= MAX_ALERTS_INTERVAL]
                else:
                    alerts_calculator[camera_id] = [] 
                alerts_calculator[camera_id].append(message_timestamp)

                if camera_id not in count_sent_messages.keys():
                    count_sent_messages[camera_id] = 0

                file_extension = pathlib.Path(event_data['videoPath']).suffix
                curr_time = round(time.time()*1000)
                imgpath = event_data['videoPath']
                filename = 'uploadedfile-sample-' + str(curr_time) + file_extension
                # imgUrl = Utils.uploadimgToS3(imgpath, filename)
                #print(imgUrl)
                
                if (len(alerts_calculator[camera_id]) >= MIN_ALERTS_THRESHOLD):
                    if count_sent_messages[camera_id] >= MAX_ALERTS_NUMBER:
                        if (message_timestamp - last_sent_timestamp[camera_id]).total_seconds()/60 > SENDING_PAUSE_TIME:
                            count_sent_messages[camera_id] = 0
                            print(f'After {SENDING_PAUSE_TIME} minutes pause we are back to sending for camera {camera_id}')
                        else:
                            print(f'Not sending message for camera {camera_id}: '
                                f'{count_sent_messages[camera_id]} messages already sent for this camera within last {SENDING_PAUSE_TIME} minutes. '
                                f'(Last sent message timestamp={last_sent_timestamp[camera_id]})')
                    if count_sent_messages[camera_id] < MAX_ALERTS_NUMBER:
                        phone_numbers = str(event_data['analyticsModule']['id']).split(';')
                        for number in phone_numbers:
                            to = number
                            msg = event_data['analyticsModule']['description'] + ' ' + event_data['sensor']['description'] + '. Please check image and press Yes to confirm fire. Press No for false alarms.'
                            print(msg)
                            # try:
                            #     resp = Utils.sendWAmsg(imgUrl,msg,headers,to)
                            #     resp.raise_for_status()
                            # except requests.exceptions.HTTPError as err:
                            #     print(err)
                            #     sys.exit(1)

                            # try:
                            #     alert_id = sqlCommands.insert_alert_detection(event.value)
                            # except Exception as e:
                            #     print(f"Error inserting alert detection: {e}")
                            #     alert_id = ''
                            # print(f"Received message - alert_id: {alert_id}")
                            # socketio.emit('new_message', {'data': event.value, 'alert_id': alert_id})

                        last_sent_timestamp[camera_id] = message_timestamp
                        count_sent_messages[camera_id]+=1
                        print(f'Message#{count_sent_messages[camera_id]} for camera {camera_id} just sent (to all whatsapp numbers)')
                else:
                    print(f'Not sending message for camera {camera_id} because it was less than {MIN_ALERTS_THRESHOLD} messages within last {MAX_ALERTS_INTERVAL} seconds')

                print("-------------------- KAFKA END ---------------------\n\n")

    except errors.NoBrokersAvailable:
        print("Warning!! Kafka server is not running. Please start the Kafka server.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")