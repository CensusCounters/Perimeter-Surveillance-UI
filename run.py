from finalfrsproject import app, socketio


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=4000, threaded=True, debug=True)
    socketio.run(app, host='0.0.0.0', port=4000, debug=True)