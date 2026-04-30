from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Our "Routing Table" mapping Usernames to their secret Session IDs
routing_table = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('register')
def handle_register(username):
    # Update the routing table with the new or updated name
    routing_table[username] = request.sid
    print(f"Registered {username} at SID: {request.sid}")

    # 1. Send EXACTLY ONE welcome message to the person who just clicked register
    emit('receive_message', {'msg': f'Welcome to the server, {username}!', 'type': 'system'}, to=request.sid)

    # 2. ITERATIVE UNICAST: Loop through the table to tell EVERYONE ELSE
    for known_user, known_sid in routing_table.items():
        # Only send the "joined" message if the SID belongs to someone else
        if known_sid != request.sid:
            emit('receive_message', {'msg': f'{username} joined the chat', 'type': 'system'}, to=known_sid)

@socketio.on('send_message')
def handle_message(data):
    recipient_name = data.get('to')
    
    # Check if the recipient exists in our routing table
    if recipient_name in routing_table:
        recipient_sid = routing_table[recipient_name]
        
        # Unicast the chat message to the recipient
        emit('receive_message', {'msg': data['msg'], 'type': 'chat'}, to=recipient_sid)
    else:
        # Unicast an error notification back to the sender
        emit('receive_message', {'msg': f'{recipient_name} is offline.', 'type': 'system'}, to=request.sid)
# --- NEW: Typing Indicator Events ---
@socketio.on('typing')
def handle_typing(data):
    recipient_name = data.get('to')
    sender_name = data.get('from')
    
    # If the recipient is online, tell them this user is typing
    if recipient_name in routing_table:
        recipient_sid = routing_table[recipient_name]
        emit('is_typing', {'sender': sender_name}, to=recipient_sid)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    recipient_name = data.get('to')
    
    # Tell the recipient to hide the typing indicator
    if recipient_name in routing_table:
        recipient_sid = routing_table[recipient_name]
        emit('stopped_typing', to=recipient_sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)