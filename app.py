import sqlite3
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

routing_table = {}

# ---Initialize Database ---
def init_db():
    # This creates a file called 'chat.db' in your folder
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender TEXT,
                  recipient TEXT,
                  message TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db() 

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('register')
def handle_register(username):
    routing_table[username] = request.sid
    print(f"Registered {username} at SID: {request.sid}")

    emit('receive_message', {'msg': f'Welcome to the server, {username}!', 'type': 'system'}, to=request.sid)

    active_users = list(routing_table.keys())

    for known_user, known_sid in routing_table.items():
        if known_sid != request.sid:
            emit('receive_message', {'msg': f'{username} joined the chat', 'type': 'system'}, to=known_sid)
        emit('update_users', {'users': active_users}, to=known_sid)

@socketio.on('disconnect')
def handle_disconnect():
    disconnected_user = None
    for username, sid in list(routing_table.items()):
        if sid == request.sid:
            disconnected_user = username
            del routing_table[username]
            break
            
    if disconnected_user:
        active_users = list(routing_table.keys())
        for known_user, known_sid in routing_table.items():
            emit('receive_message', {'msg': f'{disconnected_user} left the chat', 'type': 'system'}, to=known_sid)
            emit('update_users', {'users': active_users}, to=known_sid)

# --- Save to DB  ---
@socketio.on('send_message')
def handle_message(data):
    sender = data.get('from')
    recipient = data.get('to')
    msg = data.get('msg')
    time = data.get('time')
    
    # 1. Save to Database
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, recipient, message, timestamp) VALUES (?, ?, ?, ?)",
              (sender, recipient, msg, time))
    conn.commit()
    conn.close()
    
    # 2. Unicast to recipient if they are online
    if recipient in routing_table:
        recipient_sid = routing_table[recipient]
        emit('receive_message', {'msg': msg, 'type': 'chat', 'timestamp': time}, to=recipient_sid)
    else:
        # If offline, the message is safely in the DB! Just tell the sender.
        emit('receive_message', {'msg': f'{recipient} is offline !', 'type': 'system'}, to=request.sid)

# ---Unicast Chat History ---
@socketio.on('get_history')
def handle_history(data):
    user1 = data.get('me')
    user2 = data.get('them')

    # Ask the DB for any messages between these two specific people
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''SELECT sender, message, timestamp FROM messages
                 WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?)
                 ORDER BY id ASC''', (user1, user2, user2, user1))
    history = c.fetchall()
    conn.close()

    # Send this private history ONLY to the person who asked for it
    emit('load_history', {'history': history}, to=request.sid)

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