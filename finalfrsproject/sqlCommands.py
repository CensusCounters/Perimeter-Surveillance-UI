import psycopg2
import psycopg2.extras
from finalfrsproject import app
import os, shutil

postgres_conn = None


def connect_to_db():
    global postgres_conn
    postgres_conn = psycopg2.connect(dbname='postgres', user='postgres',
                                     password='postgres', host=app.config["POSTGRESQL_URL"])
    postgres_conn.autocommit = False


def login(user_name, password):
    global postgres_conn
    cursor = None
    result = None

    try:
        if not postgres_conn:
            connect_to_db()
            # print('Just connected to Postgres DB')

        if postgres_conn.closed != 0:
            connect_to_db()
            # print('Recreated connection')

        cursor = postgres_conn.cursor()
        # print('Created cursor')

        sql = '''SELECT user_name, user_type, id from Users where user_name = %s and password = crypt(%s,password);'''
        arg = [user_name, password]
        cursor.execute(sql, (arg))
        # print(cursor.mogrify(sql,(arg)).decode('utf=8'))
        result = cursor.fetchone()
        # return result
        result = {"Status": "Success", "Details": result}

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command", error)
        # result = error
        result = {"Status": "Fail", "Details": error}

    finally:
        # closing database connection.
        if postgres_conn:
            cursor.close()
            postgres_conn.close()
            # print("PostgreSQL connection is closed")

    return result


def get_location_list():
    global postgres_conn
    cursor = None
    result = None
    psycopg2.extras.register_uuid()

    try:
        if not postgres_conn:
            connect_to_db()
            # print('Just connected to Postgres DB')

        if postgres_conn.closed != 0:
            connect_to_db()
            # print('Recreated connection')

        cursor = postgres_conn.cursor()
        # print('Created cursor')
        sql = '''Select distinct l.location_name from locations l;'''
        arg = []
        cursor.execute(sql, (arg))
        print(cursor.mogrify(sql, (arg)).decode('utf=8'))
        result = cursor.fetchall()
        location_list_with_sub_locations = []
        location_list = []
        column_names = [desc[0] for desc in cursor.description]
        print("*****", column_names)
        if len(result) > 0:
            for location in result:
                location_list.append(dict(zip(column_names, location)))
        print("location list: ", location_list)

        result = {"Status": "Success", "Locations": location_list}

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command", error)
        result = {"Status": "Fail", "Details": error}

    finally:
        # closing database connection.
        if postgres_conn:
            cursor.close()
            postgres_conn.close()
    return result


def get_sub_location_list(location):
    global postgres_conn
    cursor = None
    result = None
    psycopg2.extras.register_uuid()

    try:
        if not postgres_conn:
            connect_to_db()
            # print('Just connected to Postgres DB')

        if postgres_conn.closed != 0:
            connect_to_db()
            # print('Recreated connection')

        cursor = postgres_conn.cursor()
        # print('Created cursor')
        sql = '''Select l.id, l.sub_location_name from locations l
                    where location_name = %s;'''
        arg = [location]
        cursor.execute(sql, (arg))
        print(cursor.mogrify(sql, (arg)).decode('utf=8'))
        result = cursor.fetchall()
        sub_location_list = []
        column_names = [desc[0] for desc in cursor.description]
        print("*****", column_names)
        if len(result) > 0:
            for location in result:
                sub_location_list.append(dict(zip(column_names, location)))
        print("location list: ", sub_location_list)

        result = {"Status": "Success", "Sub_Locations": sub_location_list}

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command", error)
        result = {"Status": "Fail", "Details": error}

    finally:
        # closing database connection.
        if postgres_conn:
            cursor.close()
            postgres_conn.close()
    return result

def get_camera_ip_address_list():
    global postgres_conn
    cursor = None
    result = None
    psycopg2.extras.register_uuid()

    try:
        if not postgres_conn:
            connect_to_db()
            # print('Just connected to Postgres DB')

        if postgres_conn.closed != 0:
            connect_to_db()
            # print('Recreated connection')

        cursor = postgres_conn.cursor()
        print('******Created cursor')
        sql = '''Select distinct c.camera_ip_address from cameras c;'''
        arg = []
        cursor.execute(sql, (arg))
        print("*****",cursor.mogrify(sql, (arg)).decode('utf=8'))
        result = cursor.fetchall()
        camera_ip_address_list = []
        column_names = [desc[0] for desc in cursor.description]
        print("*****",column_names)

        if len(result) > 0:
            for camera in result:
                camera_ip_address_list.append(dict(zip(column_names, camera)))

        print("result: ", camera_ip_address_list)
        result = {"Status": "Success", "Details": camera_ip_address_list}

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command get_camera_ip_address", error)
        result = {"Status": "Fail", "Details": error}

    #finally:
        # closing database connection.
    #    if postgres_conn:
    #        cursor_get_camera_ip_address_list.close()
    #        postgres_conn.close()
    return result


def get_detection_category_list():
    global postgres_conn
    cursor = None
    result = None
    psycopg2.extras.register_uuid()

    try:
        if not postgres_conn:
            connect_to_db()
            # print('Just connected to Postgres DB')

        if postgres_conn.closed != 0:
            connect_to_db()
            # print('Recreated connection')

        cursor = postgres_conn.cursor()
        # print('Created cursor')
        sql = '''Select distinct d.detection_category from detection_categories d;'''
        arg = []
        cursor.execute(sql, (arg))
        print(cursor.mogrify(sql, (arg)).decode('utf=8'))
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        detection_category_list = []
        if len(result) > 0:
            for detection_category in result:
                detection_category = list(detection_category)
                detection_category_list.append(dict(zip(column_names, detection_category)))
        print("result: ", detection_category_list)

        result = {"Status": "Success", "Details": detection_category_list}

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command in get_detection_category_list", error)
        result = {"Status": "Fail", "Details": error}

    finally:
        # closing database connection.
        if postgres_conn:
            cursor.close()
            postgres_conn.close()
    return result


def get_rtsp_streams():
    global postgres_conn
    cursor = None
    result = None
    psycopg2.extras.register_uuid()

    try:
        if not postgres_conn:
            connect_to_db()
            # print('Just connected to Postgres DB')

        if postgres_conn.closed != 0:
            connect_to_db()
            # print('Recreated connection')

        cursor = postgres_conn.cursor()
        # print('Created cursor')
        sql = '''Select distinct c.camera_ip_address as camera_ip_address, c.camera_rtsp_address as camera_rtsp_address, 
                    c.camera_frame_image_actual_path from cameras c where location_id = 1;'''
        arg = []
        rtsp_list = []
        cursor.execute(sql, (arg))
        print(cursor.mogrify(sql, (arg)).decode('utf=8'))
        column_names = [desc[0] for desc in cursor.description]
        result = cursor.fetchall()
        if result != None:
            if len(result) > 0:
                for camera in result:
                    camera = list(camera)
                    rtsp_list.append(dict(zip(column_names, camera)))
        # print("result: ", rtsp_list)
        result = {"Status": "Success", "Details": rtsp_list}

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command", error)
        result = {"Status": "Fail", "Details": error}

    finally:
        # closing database connection.
        if postgres_conn:
            cursor.close()
            postgres_conn.close()
    return result


def insert_new_camera_record(logged_in_user_id, camera_make, camera_ip_address, camera_username, camera_password,
                             camera_rtsp_address,
                             camera_region_of_interest, camera_associated_services, camera_roi_type, camera_location,
                             camera_frame_image_actual_path):
    global postgres_conn
    cursor = None
    result = None
    psycopg2.extras.register_uuid()
    print("sql insert stmt: ")
    try:
        if not postgres_conn:
            connect_to_db()

        if postgres_conn.closed != 0:
            connect_to_db()

        cursor = postgres_conn.cursor()
        print("sql insert stmt: ")

        sql = '''INSERT INTO cameras (created_by, camera_make, camera_ip_address, camera_username, camera_password, 
        camera_rtsp_address, camera_region_of_interest, camera_associated_services, camera_roi_is_included, 
        location_id, camera_frame_image_actual_path) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning *;'''

        arg = [logged_in_user_id, camera_make, camera_ip_address, camera_username, camera_password, camera_rtsp_address,
               camera_region_of_interest, camera_associated_services, camera_roi_type, camera_location,
               camera_frame_image_actual_path]

        result = cursor.execute(sql, (arg))
        print("sql insert stmt: ", (cursor.mogrify(sql, (arg)).decode('utf=8')))
        inserted_data = cursor.fetchone()
        postgres_conn.commit()
        count = cursor.rowcount
        print("insert count: ", count)

        result = {"Status": "Success", "Insert_Count": count, "Details": inserted_data}

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command", error)
        result = {"Status": "Fail", "Insert_Count": 0, "Details": error}

    finally:
        # closing database connection.
        if postgres_conn:
            cursor.close()
            postgres_conn.close()
            # print("PostgreSQL connection is closed")
    return result


def update_camera_record(camera_id, camera_make, camera_ip_address, camera_username, camera_password,
                         camera_rtsp_address, camera_region_of_interest,
                         camera_associated_services, camera_roi_type, camera_location_id,
                         camera_frame_image_actual_path):
    global postgres_conn
    cursor = None
    result = None
    psycopg2.extras.register_uuid()
    try:
        if not postgres_conn:
            connect_to_db()

        if postgres_conn.closed != 0:
            connect_to_db()

        cursor = postgres_conn.cursor()

        sql = '''UPDATE cameras set camera_make = %s, camera_ip_address = %s, camera_username = %s, camera_password = 
        %s, camera_rtsp_address = %s, camera_region_of_interest = %s, camera_associated_services = %s, 
        camera_roi_is_included = %s, location_id = %s, camera_frame_image_actual_path = %s where id = %s returning 
        id;'''
        arg = [camera_make, camera_ip_address, camera_username, camera_password, camera_rtsp_address,
               camera_region_of_interest,
               camera_associated_services, camera_roi_type, camera_location_id, camera_frame_image_actual_path,
               camera_id]
        cursor.execute(sql, (arg))
        print(cursor.mogrify(sql, (arg)).decode('utf=8'))
        result = cursor.fetchall()
        update_count = cursor.rowcount
        print("cameras table update count: ", update_count)
        result = {"Status": "Success", "Update_Count": update_count,
                  "Details": "Updated Camera Details for " + camera_id}
        postgres_conn.commit()

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command", error)
        result = {"Status": "Fail", "Update_Count": 0, "Details": error}

    finally:
        # closing database connection.
        if postgres_conn:
            cursor.close()
            postgres_conn.close()
            # print("PostgreSQL connection is closed")
    return result


def get_camera_list():
    global postgres_conn
    cursor = None
    result = None
    psycopg2.extras.register_uuid()

    try:
        if not postgres_conn:
            connect_to_db()
            # print('Just connected to Postgres DB')

        if postgres_conn.closed != 0:
            connect_to_db()
            # print('Recreated connection')

        cursor = postgres_conn.cursor()
        # print('Created cursor')
        sql = '''Select c.camera_make, c.camera_ip_address, c.camera_username, c.camera_password, c.camera_rtsp_address, 
                c.camera_region_of_interest, c.camera_associated_services, c.location_id, l.location_name, 
                c.camera_frame_image_actual_path, c.id, l.sub_location_name 
                from cameras c, locations l where c.location_id = l.id;'''
        arg = []
        cursor.execute(sql, (arg))
        print(cursor.mogrify(sql, (arg)).decode('utf=8'))
        column_names = [desc[0] for desc in cursor.description]
        print("column_names: ", column_names)
        result = cursor.fetchall()
        # print("result: ", result[0])
        camera_list = []
        for camera in result:
            camera = dict(zip(column_names, camera))
            camera_list.append(camera)
        # print("all_cameras: ", camera_list)
        result = {"Status": "Success", "Details": camera_list}

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command", error)
        result = {"Status": "Fail", "Details": error}

    finally:
        # closing database connection.
        if postgres_conn:
            cursor.close()
            postgres_conn.close()
    return result


def get_camera_details(camera_id):
    global postgres_conn
    cursor = None
    result = None
    psycopg2.extras.register_uuid()

    try:
        if not postgres_conn:
            connect_to_db()
            # print('Just connected to Postgres DB')

        if postgres_conn.closed != 0:
            connect_to_db()
            # print('Recreated connection')

        cursor = postgres_conn.cursor()
        # print('Created cursor')
        sql = '''Select c.camera_make, c.camera_ip_address, c.camera_username, c.camera_password, 
        c.camera_rtsp_address, c.camera_region_of_interest, c.camera_associated_services, c.location_id, 
        l.location_name, c.camera_frame_image_actual_path, c.id, l.sub_location_name from cameras c, locations l 
        where c.id = %s and c.location_id = l.id;'''

        arg = [camera_id, ]
        cursor.execute(sql, (arg))
        print(cursor.mogrify(sql, (arg)).decode('utf=8'))
        result = cursor.fetchone()
        column_names = [desc[0] for desc in cursor.description]
        result = dict(zip(column_names, result))

        # print("all_trips: ", result)
        result = {"Status": "Success", "Details": result}

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command", error)
        result = {"Status": "Fail", "Details": error}

    finally:
        # closing database connection.
        if postgres_conn:
            cursor.close()
            postgres_conn.close()
    return result


def get_detections_by_date(start_date, end_date, camera_ip_address, detection_category):
    global postgres_conn
    sql = None
    arg = None
    cursor = None
    result = None
    psycopg2.extras.register_uuid()
    print(camera_ip_address)
    print(detection_category)

    try:
        if not postgres_conn:
            connect_to_db()

        if postgres_conn.closed != 0:
            connect_to_db()

        cursor = postgres_conn.cursor()

        if camera_ip_address == 'All' and detection_category == 'All':
            sql = ''' select c.camera_ip_address as camera_ip_address, d.date_created as detection_time, d.frame_id as frame_id, 
                        d.detection_model as detection_model, d.detection_category as detection_category, 
                        d.bounding_boxes as bounding_box, detection_image_location as detection_image_location, 
                        d.was_alert_sent as alert_status, d.alert_id as alert_time from detections d, cameras c
                        where d.date_created between %s and %s
                        and c.id = d.camera_id
                        order by d.date_created desc; '''
            arg = [start_date, end_date]
        elif camera_ip_address == 'All' and detection_category != 'All':
            sql = ''' select c.camera_ip_address as camera_ip_address, d.date_created as detection_time, d.frame_id as frame_id, 
                        d.detection_model as detection_model, d.detection_category as detection_category, 
                        d.bounding_boxes as bounding_box, detection_image_location as detection_image_location, 
                        d.was_alert_sent as alert_status, d.alert_id as alert_time from detections d, cameras c
                        where d.date_created between %s and %s
                        and c.id = d.camera_id
                        and d.detection_category = %s
                        order by d.date_created desc; '''
            arg = [start_date, end_date, detection_category]
        else:
            sql = ''' select c.camera_ip_address as camera_ip_address, d.date_created as detection_time, d.frame_id as frame_id, 
                        d.detection_model as detection_model, d.detection_category as detection_category, 
                        d.bounding_boxes as bounding_box, detection_image_location as detection_image_location, 
                        d.was_alert_sent as alert_status, d.alert_sent_time as alert_time from detections d, cameras c
                        where d.date_created between %s and %s
                        and c.id = d.camera_id
                        and c.camera_ip_address = %s
                        order by d.date_created desc; '''
            arg = [start_date, end_date, camera_ip_address]

        cursor.execute(sql, arg)
        print(cursor.mogrify(sql, arg).decode('utf=8'))
        column_names = [desc[0] for desc in cursor.description]
        result = cursor.fetchall()
        detection_list = []
        print("result: ", result)

        if len(result) > 0:
            for detection in result:
                detection = list(detection)
                if detection[1] is not None:
                    detection_time = detection[1].strftime('%d %b, %Y %I:%M %p')  # strftime('%d-%m-%Y %H:%M:%S')
                    detection[1] = detection_time

                if detection[6] is not None:
                    detection_image_location = os.path.sep.join(
                        [app.config["KNOWN_DETECTION_PATH_FOR_HTML"], os.path.basename(detection[6].rstrip('/'))])
                    detection[6] = detection_image_location

                if detection[8] is not None:
                    alert_time = detection[8].strftime('%d %b, %Y %I:%M %p')  # strftime('%d-%m-%Y %H:%M:%S')
                    detection[8] = alert_time

                detection_list.append(dict(zip(column_names, detection)))
        else:
            print("No records found")
            detection_list.append({
                'camera_ip_address': 'No records found',
                'detection_date': 'No records found',
                'frame_id': 'No records found',
                'detection_time': 'No records found',
                'detection_model': 'No records found',
                'detection_category': 'No records found',
                'bounding_box': 'No records found',
                'alert_status': 'No records found',
                'alert_time': 'No records found'
            })

        # print("detection_list: ", detection_list)
        result = {"Status": "Success", "Details": detection_list}

    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command", error)
        result = {"Status": "Fail", "Details": error}

    finally:
        if postgres_conn:
            cursor.close()
            postgres_conn.close()

    return result
