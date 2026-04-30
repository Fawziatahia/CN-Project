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

    # Send EXACTLY ONE welcome message
    emit('receive_message', {'msg': f'Welcome to the server, {username}!', 'type': 'system'}, to=request.sid)

    # Get the current list of all active users
    active_users = list(routing_table.keys())

    # Tell EVERYONE the new user joined, and give them the updated user list
    for known_user, known_sid in routing_table.items():
        if known_sid != request.sid:
            emit('receive_message', {'msg': f'{username} joined the chat', 'type': 'system'}, to=known_sid)
        
        # Send the updated list to EVERYONE (including the person who just joined)
        emit('update_users', {'users': active_users}, to=known_sid)


@socketio.on('disconnect')
def handle_disconnect():
    disconnected_user = None
    
    # Find which user belonged to the SID that just disconnected
    for username, sid in list(routing_table.items()):
        if sid == request.sid:
            disconnected_user = username
            del routing_table[username] 
            break
            
    if disconnected_user:
        print(f"Disconnected: {disconnected_user}")
        active_users = list(routing_table.keys())
        
        # Tell everyone else that they left, and send the new, smaller user list
        for known_user, known_sid in routing_table.items():
            emit('receive_message', {'msg': f'{disconnected_user} left the chat', 'type': 'system'}, to=known_sid)
            emit('update_users', {'users': active_users}, to=known_sid)

@socketio.on('send_message')
def handle_message(data):
    recipient_name = data.get('to')
    
    if recipient_name in routing_table:
        recipient_sid = routing_table[recipient_name]
        emit('receive_message', {'msg': data['msg'], 'type': 'chat'}, to=recipient_sid)
    else:
        emit('receive_message', {'msg': f'{recipient_name} is offline.', 'type': 'system'}, to=request.sid)

@socketio.on('typing')
def handle_typing(data):
    recipient_name = data.get('to')
    sender_name = data.get('from')
    if recipient_name in routing_table:
        recipient_sid = routing_table[recipient_name]
        emit('is_typing', {'sender': sender_name}, to=recipient_sid)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    recipient_name = data.get('to')
    if recipient_name in routing_table:
        recipient_sid = routing_table[recipient_name]
        emit('stopped_typing', to=recipient_sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)