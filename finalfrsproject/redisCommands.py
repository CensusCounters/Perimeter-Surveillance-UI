import redis
import json
from finalfrsproject import redisCommands

# Connect to Redis
#redis_conn = redis.from_url('redis://census_counters-redis:6379')
redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0)
#print("redis_conn: ", redis_conn)


def create_json_for_known_person_get_from_redis_object(user_id, user_name, user_type):
	session_values_json_redis = json.loads(redis_conn.get(user_id))
	#print("redis object in known person get: ", session_values_json_redis)
	send_to_html_json = {
        'details_entered_by': session_values_json_redis.get("details_entered_by"),
        'details_entered_on': session_values_json_redis.get("details_entered_on"),
        'person_name': session_values_json_redis.get("person_name"),
        'original_img' : session_values_json_redis.get("person_image"),
        'fathers_name': session_values_json_redis.get("fathers_name"),
        'resident_of': session_values_json_redis.get("resident_of"),
        'aadhar_number': session_values_json_redis.get("aadhar_number"),
        'aadhar_image': session_values_json_redis.get("aadhar_image"),
        'drivers_license': session_values_json_redis.get("drivers_license"),
        'drivers_license_image': session_values_json_redis.get("drivers_license_image"),
        'person_id': session_values_json_redis.get("person_id"),
        'person_image': session_values_json_redis.get("person_image"),
        'message': session_values_json_redis.get('message'),
        #'message': 'Success! Visitor Information is in the database. Please continue.',
        'logged_in_user': user_name,
        'logged_in_user_type': user_type,
        'page_title': 'Known Visitor'
    }
	return send_to_html_json

def create_json_for_unknown_person_get_from_redis_object(user_id, user_name, user_type):
	session_values_json_redis = json.loads(redis_conn.get(user_id))
	#print("redis object in unknown person get: ", session_values_json_redis)
	send_to_html_json = {
		'img': session_values_json_redis.get('person_image_html_path'),
		'person_image_actual_path': session_values_json_redis.get('person_image_actual_path'),
		'enrollment_id': session_values_json_redis.get('enrollment_id'),
		'traveler_type': session_values_json_redis.get('traveler_type'),
		'aadhar_number': session_values_json_redis.get('aadhar_number'),
		#'message': 'This person is not in the system. Please enter details and submit.',
		'message': session_values_json_redis.get('message'),
		'logged_in_user': user_name,
		'logged_in_user_type': user_type,
		'page_title': "Unknown Person"    
	}
	return send_to_html_json

def create_json_for_trip_registration_post_from_redis_object(user_id, entry_time):
	session_values_json_redis = json.loads(redis_conn.get(user_id))
	#print("redis object in trip registration post: ", session_values_json_redis)
	send_to_html_json = {
        'person_id': session_values_json_redis.get("person_id"),
        'person_image': session_values_json_redis.get("person_image"),
        'vehicle_image': session_values_json_redis.get("vehicle_image"),
        'traveler_name': session_values_json_redis.get("person_name"),
        'traveler_type': session_values_json_redis.get("traveler_type"),
        'vehicle_number': session_values_json_redis.get("vehicle_plate_number"),
        'coming_from': session_values_json_redis.get("coming_from"),
        'going_to' : session_values_json_redis.get("going_to"),
        'entry_time': entry_time,
        'male_passengers': session_values_json_redis.get("male_passengers"),
        'female_passengers': session_values_json_redis.get("female_passengers"),
        'child_passengers': session_values_json_redis.get("child_passengers"),
        'trip_reason': session_values_json_redis.get("trip_reason"),
        'trip_type': session_values_json_redis.get("trip_type"),
        'permit_image': session_values_json_redis.get("permit_image")
    }
	return send_to_html_json

def create_json_for_trip_registration_get_from_redis_object(user_id, user_name, user_type, entry_time):
	session_values_json_redis = json.loads(redis_conn.get(user_id))
	#print("redis object in trip registration get: ", session_values_json_redis)
	send_to_html_json = {
	    'person_id': session_values_json_redis.get('person_id'),
	    'person_name': session_values_json_redis.get('person_name'),
	    'person_image': session_values_json_redis.get('person_image'),
	    'traveler_type': session_values_json_redis.get('traveler_type'),
	    'vehicle_plate_number': session_values_json_redis.get('vehicle_plate_number'),
	    'vehicle_image': session_values_json_redis.get('vehicle_image'),
	    'driver_trip_id': session_values_json_redis.get('driver_trip_id'),
	    'entry_time': entry_time,
	    'message': 'Please select traveler type and enter trip details.',
	    'logged_in_user': user_name,
	    'logged_in_user_type': user_type,
	    'page_title': 'Add Trip'
	}	
	return send_to_html_json

def create_json_for_make_trip_summary_get_from_redis_object(user_id, user_name, user_type):
	session_values_json_redis = json.loads(redis_conn.get(user_id))
	#print("redis object in make trip summary get: ", session_values_json_redis)
	send_to_html_json = {
	    'trip_and_traveler_details': session_values_json_redis.get("trip_and_traveler_details"),
	    #'message': 'Trip popd Successfully. Click Continue to return to the home page.',
	    'message': session_values_json_redis.get("message"),
	    'logged_in_user': user_name,
	    'logged_in_user_type': user_type,
	    'page_title': "Trip Summary"
	}	
	return send_to_html_json

def create_json_for_recognize_vehicle_get_from_redis_object(user_id, user_name, user_type):
	session_values_json_redis = json.loads(redis_conn.get(user_id))
	#print("redis object in recognize vehicle get: ", session_values_json_redis)
	send_to_html_json = {
	    'status': 'Success',
	    'unregistered_vehicles': session_values_json_redis.get('unregistered_vehicles'),
	    'traveler_type': session_values_json_redis.get('traveler_type'),
	    'logged_in_user': user_name,
	    'logged_in_user_type': user_type,
	    'page_title': "Unknown Vehicle",
	    #'message': 'Please identify the vehicle from the list below.'
	    'message': session_values_json_redis.get('message')
	}
	return send_to_html_json

def create_json_for_recognize_trip_get_from_redis_object(user_id, user_name, user_type):
	session_values_json_redis = json.loads(redis_conn.get(user_id))
	#print("redis object in recognize trip get: ", session_values_json_redis)
	send_to_html_json = {
		'status': 'Success',
		'open_trips': session_values_json_redis.get('open_trips'),          
		'logged_in_user': user_name,
		'logged_in_user_type': user_type,
		'page_title': "Unknown Trip",
		'message': 'Please select a trip from the list below.'	
	}
	return send_to_html_json

def create_json_for_unknown_vehicle_get_from_redis_object(user_id,user_name,user_type):
	session_values_json_redis = json.loads(redis_conn.get(user_id))
	#print("redis object in unknown vehicle get: ", session_values_json_redis)

	send_to_html_json = {
		'vehicle_id': session_values_json_redis.get('vehicle_id'),
        'vehicle_number': session_values_json_redis.get('vehicle_plate_number'),
        'vehicle_image_url': session_values_json_redis.get('vehicle_image_html_path'),

        'vehicle_make': session_values_json_redis.get("vehicle_make"),
        'vehicle_model': session_values_json_redis.get("vehicle_model"),
        'vehicle_color': session_values_json_redis.get("vehicle_color"),
        'vehicle_entry_time': session_values_json_redis.get("vehicle_entry_time"),
        'vehicle_exit_time': session_values_json_redis.get("pop_time"),
    
        'logged_in_user': user_name,
        'logged_in_user_type': user_type,
        'page_title' : 'Unregistered Vehicle',
        #'message': 'Please review and click submit to save the vehicle data.'
        'message': session_values_json_redis.get('message')
	}
	return send_to_html_json

def create_json_for_known_vehicle_get_from_redis_object(user_id,user_name,user_type):
	session_values_json_redis = json.loads(redis_conn.get(user_id))
	#print("redis object in known vehicle get: ", session_values_json_redis)

	send_to_html_json = {
            'vehicle_number': session_values_json_redis.get("vehicle_plate_number"),
            'vehicle_image_url': session_values_json_redis.get('vehicle_image'),
            'vehicle_make': session_values_json_redis.get("vehicle_make"),
            'vehicle_model': session_values_json_redis.get("vehicle_model"),
            'vehicle_color': session_values_json_redis.get("vehicle_color"),
            'vehicle_type': session_values_json_redis.get("vehicle_type"),
            'vehicle_owner': session_values_json_redis.get("vehicle_owner"),
            'vehicle_registration_date': session_values_json_redis.get("vehicle_registration_date"),
            'vehicle_expiry_date': session_values_json_redis.get("vehicle_expiry_date"),
            'logged_in_user': user_name,
            'logged_in_user_type': user_type,
            'page_title' : 'Registered Vehicle',
            'message': 'Success! Vehicle Information is in the database. Please continue.',
            'success_font': 'True'
        }
	return send_to_html_json

def clean_redis_object(user_id):

	session_values_json_redis = json.loads(redis_conn.get(user_id))
	#print("redis object in trip registration before clean up: ", session_values_json_redis)


	session_values_json_redis.pop('person_id','Not found')
	session_values_json_redis.pop('enrollment_id','Not found')
	session_values_json_redis.pop('person_image','Not found')
	session_values_json_redis.pop('message','Not found')
	session_values_json_redis.pop('traveler_type','Not found')
	session_values_json_redis.pop("person_image_html_path")
	session_values_json_redis.pop('person_image_actual_path')
	session_values_json_redis.pop('person_name','Not found')
	session_values_json_redis.pop('fathers_name','Not found')
	session_values_json_redis.pop('resident_of','Not found')
	session_values_json_redis.pop('aadhar_number','Not found')
	session_values_json_redis.pop('aadhar_image','Not found')
	session_values_json_redis.pop('drivers_license','Not found')
	session_values_json_redis.pop('drivers_license_image','Not found')
	#if session_values_json_redis.get('unregistered_vehicles') is not None:
	session_values_json_redis.pop('unregistered_vehicles','Not found')
	session_values_json_redis.pop('vehicle_image_html_path','Not found')
	session_values_json_redis.pop('vehicle_image_actual_path','Not found')
	session_values_json_redis.pop('vehicle_image','Not found')
	session_values_json_redis.pop('vehicle_id','Not found')
	session_values_json_redis.pop('vehicle_plate_number','Not found')
	session_values_json_redis.pop('vehicle_make','Not found')
	session_values_json_redis.pop('vehicle_model','Not found')
	session_values_json_redis.pop('vehicle_entry_time','Not found')
	session_values_json_redis.pop('vehicle_exit_time','Not found')
	session_values_json_redis.pop('vehicle_color','Not found')
	session_values_json_redis.pop('vehicle_type','Not found')
	session_values_json_redis.pop('coming_from','Not found')
	session_values_json_redis.pop('going_to','Not found')
	session_values_json_redis.pop('entry_time','Not found')
	#session_values_json_redis.pop('male_passengers')
	session_values_json_redis.pop('female_passengers','Not found')
	session_values_json_redis.pop('child_passengers','Not found')
	session_values_json_redis.pop('trip_reason','Not found')
	session_values_json_redis.pop( 'trip_type','Not found')
	session_values_json_redis.pop('permit_image','Not found')
	session_values_json_redis.pop('trip_id','Not found')
	session_values_json_redis.pop("person_details",'Not found')
	#session_values_json_redis.pop('driver_trip_id')
	#print("redis object in trip registration after clean up: ", session_values_json_redis)

	return session_values_json_redis 


def clean_redis_object_before_aadhar_lookup(session_values_json_redis):
    
	session_values_json_redis.pop("person_image_html_path",'Not found') 
	session_values_json_redis.pop("person_image_actual_path", 'Not found')
	session_values_json_redis.pop("details_entered_by",'Not found')
	session_values_json_redis.pop("details_entered_on",'Not found')
	session_values_json_redis.pop("person_name",'Not found')
	session_values_json_redis.pop("fathers_name",'Not found')
	session_values_json_redis.pop("resident_of",'Not found')
	session_values_json_redis.pop("aadhar_number",'Not found')
	session_values_json_redis.pop("aadhar_image",'Not found')
	session_values_json_redis.pop("drivers_license",'Not found')
	session_values_json_redis.pop("drivers_license_image",'Not found')
	session_values_json_redis.pop("person_id",'Not found')
	session_values_json_redis.pop("enrollment_id",'Not found')
	session_values_json_redis.pop("person_image",'Not found')
	session_values_json_redis.pop("person_details",'Not found')
	
	return session_values_json_redis 