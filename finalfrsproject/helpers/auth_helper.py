import json
from flask import render_template, redirect, url_for, make_response
from flask_jwt_extended import create_access_token, set_access_cookies
from finalfrsproject import sqlCommands, redisCommands

def fetch_user_details(username, password):
    """Attempt to fetch user details from the database."""
    return sqlCommands.login(username, password)

def get_redis_session(user_id, app_name):
    """Fetch session details from Redis if available."""
    redis_key = f"{user_id}{app_name}"
    session_data = redisCommands.redis_conn.get(redis_key)
    if session_data:
        return json.loads(session_data)
    return {}

def create_identity(details):
    """Create identity dictionary for JWT token."""
    return {
        "logged_in_user_name": details[0],
        "logged_in_user_type": details[1],
        "logged_in_user_id": details[2],
        "redis_parent_key": str(details[2]) + "platform_ui",
        "application_name": "platform_ui"
    }

def login_response(details, destination="home"):
    """Create response for successful login."""
    access_token = create_access_token(identity=create_identity(details))
    response = make_response(redirect(url_for(destination)))
    set_access_cookies(response, access_token)
    return response

def error_response(page_title, message, template='login.html', status_code=200):
    """Create error response."""
    return render_template(template, details={'page_title': page_title, 'message': message}), status_code

def save_session_to_redis(key, value):
    """Save session data to Redis."""
    redisCommands.redis_conn.set(key, json.dumps(value))

def delete_session_from_redis(key):
    """Delete session data from Redis."""
    redisCommands.redis_conn.delete(key)

def get_session_from_redis(key):
    """Retrieve session data from Redis."""
    session_data = redisCommands.redis_conn.get(key)
    return json.loads(session_data) if session_data else None

def logout_get(jwt_details):
    message = 'Do you want to save the current progress and start from this point next time you log in?'
    send_to_html_json = {
        'logged_in_user': jwt_details.get("logged_in_user_name"),
        'logged_in_user_type': jwt_details.get("logged_in_user_type"),
        'message': message,
        'page_title': 'Logout'
    }
    return render_template('logout.html', details=send_to_html_json)

def logout_post(jwt_details, request, unset_jwt_cookies):
    redis_parent_key = jwt_details.get('redis_parent_key')
    session_values_json_redis = None
    if redisCommands.redis_conn.get(redis_parent_key) is not None:
        session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))

    form = request.form

    if form.get('Yes') == 'Yes':
        print('redis in logout when save redis is selected: ', session_values_json_redis)
        response = make_response(redirect(url_for('login')))
        unset_jwt_cookies(response)
        return response

    else:
        redisCommands.redis_conn.delete(redis_parent_key)
        if redisCommands.redis_conn.get(redis_parent_key) is not None:
            session_values_json_redis = json.loads(redisCommands.redis_conn.get(redis_parent_key))
            print('redis in logout when delete redis is selected: ', session_values_json_redis)
        else:
            print('redis in logout after redis is deleted')
        response = make_response(redirect(url_for('login')))
        unset_jwt_cookies(response)
        return response

