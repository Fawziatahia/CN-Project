from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

routing_table = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('register')
def handle_register(username):
    routing_table[username] = request.sid
    print(f"Registered {username} at SID: {request.sid}")

    for known_user, known_sid in routing_table.items():
        if known_sid != request.sid:
            # Notify other users that a new person joined
            emit('receive_message', {'msg': f'{username} joined the chat', 'type': 'system'}, to=known_sid)
        else:
            #a welcome message
            emit('receive_message', {'msg': f'Welcome to the server, {username}!', 'type': 'system'}, to=known_sid)

@socketio.on('send_message')
def handle_message(data):
    recipient_name = data.get('to')
    
    if recipient_name in routing_table:
        recipient_sid = routing_table[recipient_name]
        emit('receive_message', {'msg': data['msg'], 'type': 'chat'}, to=recipient_sid)
    else:
        # Unicast an error notification back to the sender
        emit('receive_message', {'msg': f'{recipient_name} is not online.', 'type': 'system'}, to=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)