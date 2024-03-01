from datetime import datetime
import uuid, json
from .auth_helper import save_session_to_redis, get_session_from_redis, delete_session_from_redis

def process_home_form(redis_parent_key, form, redis_conn):
    """
    Process the form submission from the home page and update Redis accordingly.
    """
    ticket_status = None
    next_page = None

    if form.get('add_camera'):
        ticket_status = "add_camera"
        next_page = 'add_camera'
    elif form.get('edit_camera'):
        ticket_status = "list_camera"
        next_page = 'list_camera'
    elif form.get('view_reports'):
        ticket_status = "report_home"
        next_page = 'report_home'
    session_values_json_redis = json.loads(redis_conn.get(redis_parent_key))

    session_values_json_redis.update({"ticket_status": ticket_status})
    save_session_to_redis(redis_parent_key, session_values_json_redis)

    return next_page

def get_home_details(redis_parent_key, jwt_details, method):
    """
    Prepare the details for rendering the home template based on the request method.
    """
    ticket_id = str(uuid.uuid4())
    ticket_start_time = datetime.now().isoformat()
    logged_in_user_id = jwt_details.get('logged_in_user_id')

    session_values_json_redis = {
        "ticket_id": ticket_id,
        "ticket_start_time": ticket_start_time,
        "logged_in_user_id": logged_in_user_id
    }
    save_session_to_redis(redis_parent_key, session_values_json_redis)
    print("redis in home: ", session_values_json_redis)
    message = 'Please click on one of the options below to continue.' + \
               ' This will start a new thread.' if method == 'GET' else \
               'Please click on one of the options below to continue.'
    return {
        'logged_in_user': jwt_details.get("logged_in_user_name"),
        'logged_in_user_type': jwt_details.get("logged_in_user_type"),
        'message': message,
        'page_title': 'Home Page'
    }
