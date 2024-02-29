from finalfrsproject import app, jwt
from flask_jwt_extended import get_jwt_identity, get_jwt, jwt_required
from flask import render_template, jsonify
from flask_wtf.csrf import CSRFError


@app.errorhandler(404)
#@jwt_required()
def not_found_error(error):
    print("In not_found_error")
    #jwt_details=get_jwt_identity()
    #print("token: ", jwt_details)
    send_to_html_json = {
        #'logged_in_user':  jwt_details.get("logged_in_user_name"),
        #'logged_in_user_type': jwt_details.get("logged_in_user_type"),
        'message': 'System encountered a file not found error. The administration has been notified. Use the link below to continue.',
        'page_title': 'Error'
    }
    print("404 error details: ", send_to_html_json)
    return render_template('404.html', details=send_to_html_json), 404


@app.errorhandler(401)
#@jwt_required()
def not_found_error(error):
    print("In 401")
    #jwt_details=get_jwt_identity()
    #print("token: ", jwt_details)
    send_to_html_json = {
    #    'logged_in_user':  jwt_details.get("logged_in_user_name"),
    #    'logged_in_user_type': jwt_details.get("logged_in_user_type"),
        'message': 'System encountered a file not found error. The administration has been notified. Use the link below to continue.',
        'page_title': 'Error'
    }
    print("404 error details: ", send_to_html_json)
    return render_template('401.html', details=send_to_html_json), 401    


@app.errorhandler(500)
#@jwt_required()
def internal_server_error(error):
    print("In internal server_error")
#    jwt_details=get_jwt_identity()
#    print("token: ", jwt_details)
    send_to_html_json = {
#        'logged_in_user':  jwt_details.get("logged_in_user_name"),
#        'logged_in_user_type': jwt_details.get("logged_in_user_type"),
        'message': 'An unexpected errror has been encountered. The administration has been notified. Use the link below to continue.',
        'page_title': 'Error'
    }
    print("500 error details: ", send_to_html_json)
    return render_template('500.html', details=send_to_html_json), 500


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    print("csrf error")
    send_to_html_json = {
        'message': 'You have been logged out due to inactivity. Please login again.',
        'page_title': 'Error',
        'redirect': "url_for('login')"
    }
    print("expired csrf details: ", send_to_html_json)
    return render_template('token_error.html', details=send_to_html_json), 400
    #return render_template('csrf_error.html', reason=e.description), 400


#@app.errorhandler(CustomException)
#@jwt_required()
#def custom_exception(error):
    #response = jsonify(error.to_dict())
    #response.status_code = error.status_code
    #return response
#    print("In custom exception")
#    jwt_details=get_jwt_identity()
#    print("token: ", jwt_details)
    
#    send_to_html_json = {
#        'logged_in_user':  jwt_details.get("logged_in_user_name"),
#        'logged_in_user_type': jwt_details.get("logged_in_user_type"),
#        'message': 'An unexpected errror has been encountered. The administration has been notified. Use the link below to continue.',
#        'page_title': 'Error'
#    }
#    print("customr_exception: ", send_to_html_json)
#    return render_template('500.html', details=send_to_html_json), 500        

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    send_to_html_json = {
        'message': 'The token has expired. Please login again.',
        'page_title': 'Error',
        'redirect': "url_for('login')"
    }
    print("expired_token details: ", send_to_html_json)
    return render_template('token_error.html', details=send_to_html_json), 401
    
    #return redirect(url_for('login'))        
    #return (
    #    jsonify({"message": "The token has expired.", "error": "token_expired"}),
    #    401,
    #)

@jwt.invalid_token_loader
def invalid_token_callback(error):
    send_to_html_json = {
        'message': 'The token has expired. Please login again.',
        'page_title': 'Error'
    }
    print("invalid_token details: ", send_to_html_json)
    return render_template('token_error.html', details=send_to_html_json), 401
    
    #return redirect(url_for('login'))        

    #return (jsonify({"message": "Signature verification failed.", "error": "invalid_token"}),401,)

@jwt.unauthorized_loader
def missing_token_callback(error):
    send_to_html_json = {
        'message': 'The token has expired. Please login again.',
        'page_title': 'Error'
    }
    print("missing token details: ", send_to_html_json)
    return render_template('token_error.html', details=send_to_html_json), 401
    #return (jsonify({"description": "Request does not contain an access token.","error": "authorization_required",}),401,)

'''
app.errorhandler(Exception)
@jwt_required()
def custom_exception(error):
    print("In custom exception")
    jwt_details=get_jwt_identity()
    print("token: ", jwt_details)
    send_to_html_json = {
        'logged_in_user':  jwt_details.get("logged_in_user_name"),
        'logged_in_user_type': jwt_details.get("logged_in_user_type"),
        'message': 'An unexpected errror has been encountered. The administration has been notified. Use the link below to continue.',
        'page_title': 'Error'
    }
    print("customr_exception: ", send_to_html_json)
    return render_template('500.html', details=send_to_html_json), 500        
'''