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
            #print('Just connected to Postgres DB')
    
        if postgres_conn.closed != 0:
            connect_to_db()
            #print('Recreated connection')
        
        cursor = postgres_conn.cursor()
        #print('Created cursor')

        sql = '''SELECT user_name, user_type, id from Users where user_name = %s and password = crypt(%s,password);'''
        arg = [user_name,password]
        cursor.execute(sql,(arg))
        #print(cursor.mogrify(sql,(arg)).decode('utf=8'))
        result = cursor.fetchone()
        #return result
        result = {"Status": "Sucess", "Details": result}
     
    except (Exception, psycopg2.Error) as error:
        print("Error while executing PostgreSQL command", error)
        #result = error
        result = {"Status": "Fail", "Details": error}
 
    finally:
        # closing database connection.
        if postgres_conn:
            cursor.close()
            postgres_conn.close()
            #print("PostgreSQL connection is closed")

    return result

def insert_new_camera_record(logged_in_user_id, camera_make, camera_ip_address, camera_username, camera_password, camera_rtsp_address,
                             camera_region_of_interest, camera_associated_services, camera_roi_type):
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

        sql = ''' INSERT INTO cameras (created_by, camera_make, camera_ip_address, camera_username, camera_password, 
                camera_rtsp_address, camera_region_of_interest, camera_associated_services, camera_roi_is_included) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) returning *; '''

        arg = [logged_in_user_id, camera_make, camera_ip_address, camera_username, camera_password, camera_rtsp_address,
               camera_region_of_interest, camera_associated_services, camera_roi_type]

        result = cursor.execute(sql, (arg))
        print("sql insert stmt: ", (cursor.mogrify(sql,(arg)).decode('utf=8')))
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

def update_camera_record(camera_id, camera_make, camera_ip_address, camera_username, camera_password):
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

        sql = ''' UPDATE cameras set camera_make = %s, camera_ip_address = %s, camera_username = %s, camera_password = %s 
                where id = %s returning id; '''
        arg = [camera_make, camera_ip_address, camera_username, camera_password, camera_id]
        cursor.execute(sql, (arg))
        print(cursor.mogrify(sql, (arg)).decode('utf=8'))
        result = cursor.fetchall()
        updated_id = result[0]
        update_count = cursor.rowcount
        print("vehicles table update count: ", update_count)
        postgres_conn.commit()
        if update_count > 0:
            result = {"Status": "Success", "Update_Count": update_count, "Details": "Updated Camera Details for " + camera_id}

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
        sql = '''Select c.camera_make, c.camera_ip_address, c.camera_username, c.camera_password, c.camera_rtsp_address, c.camera_region_of_interest, 
                    c.camera_associated_services, c.id from cameras c;'''
        arg = []
        cursor.execute(sql, (arg))
        print(cursor.mogrify(sql,(arg)).decode('utf=8'))
        result = cursor.fetchall()
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
        sql = '''Select c.camera_make, c.camera_ip_address, c.camera_username, c.camera_password, c.camera_rtsp_address, c.camera_region_of_interest, 
                    c.camera_associated_services, c.id from cameras c where c.id = %s;'''
        arg = [camera_id,]
        cursor.execute(sql, (arg))
        print(cursor.mogrify(sql,(arg)).decode('utf=8'))
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
