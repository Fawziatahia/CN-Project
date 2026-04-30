import sqlite3
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

routing_table = {}

def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    # NEW: Added 'date' column
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender TEXT,
                  recipient TEXT,
                  message TEXT,
                  timestamp TEXT,
                  date TEXT,
                  status TEXT DEFAULT 'sent')''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

init_db()

def broadcast_users():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    all_users = [row[0] for row in c.fetchall()]
    conn.close()

    online_users = list(routing_table.keys())
    offline_users = [u for u in all_users if u not in online_users]

    socketio.emit('update_users', {'online': online_users, 'offline': offline_users})

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('register')
def handle_register(username):
    routing_table[username] = request.sid

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

    emit('receive_message', {'msg': f'Welcome back, {username}!', 'type': 'system'}, to=request.sid)

    for known_user, known_sid in routing_table.items():
        if known_sid != request.sid:
            emit('receive_message', {'msg': f'{username} joined the chat', 'type': 'system'}, to=known_sid)

    broadcast_users()

@socketio.on('disconnect')
def handle_disconnect():
    disconnected_user = None
    for username, sid in list(routing_table.items()):
        if sid == request.sid:
            disconnected_user = username
            del routing_table[username]
            break

    if disconnected_user:
        for known_user, known_sid in routing_table.items():
            emit('receive_message', {'msg': f'{disconnected_user} left the chat', 'type': 'system'}, to=known_sid)

        broadcast_users()

@socketio.on('send_message')
def handle_message(data):
    sender = data.get('from')
    recipient = data.get('to')
    msg = data.get('msg')
    time = data.get('time')
    date = data.get('date') # NEW: Grab the date from the frontend

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    # NEW: Insert the date into the database
    c.execute("INSERT INTO messages (sender, recipient, message, timestamp, date, status) VALUES (?, ?, ?, ?, ?, 'sent')",
              (sender, recipient, msg, time, date))
    conn.commit()
    conn.close()

    if recipient in routing_table:
        recipient_sid = routing_table[recipient]
        # NEW: Send the date along to the recipient
        emit('receive_message', {'msg': msg, 'type': 'chat', 'sender': sender, 'timestamp': time, 'date': date}, to=recipient_sid)
    else:
        emit('receive_message', {'msg': f'{recipient} is offline !', 'type': 'system'}, to=request.sid)

@socketio.on('mark_read')
def handle_mark_read(data):
    sender = data.get('sender')
    recipient = data.get('recipient')

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("UPDATE messages SET status='read' WHERE sender=? AND recipient=? AND status='sent'", (sender, recipient))
    conn.commit()
    conn.close()

    if sender in routing_table:
        emit('messages_read', {'reader': recipient}, to=routing_table[sender])

@socketio.on('get_history')
def handle_history(data):
    user1 = data.get('me')
    user2 = data.get('them')

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    # NEW: Fetch the date column (index 4)
    c.execute('''SELECT sender, message, timestamp, status, date FROM messages
                 WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?)
                 ORDER BY id ASC''', (user1, user2, user2, user1))
    history = c.fetchall()
    conn.close()

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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)