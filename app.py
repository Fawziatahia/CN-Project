import sqlite3
import time
import threading
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = 'talknest-dev-secret-key'
socketio = SocketIO(app)

routing_table = {}
user_presence = {}
cached_all_users = []
cache_timestamp = 0

def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
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

def migrate_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE messages ADD COLUMN date TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE messages ADD COLUMN status TEXT DEFAULT 'sent'")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

migrate_db()

def get_all_users():
    global cached_all_users, cache_timestamp
    now = time.time()
    if now - cache_timestamp > 5 or not cached_all_users:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("SELECT username FROM users")
        cached_all_users = [row[0] for row in c.fetchall()]
        conn.close()
        cache_timestamp = now
    return cached_all_users

def broadcast_users():
    all_users = get_all_users()
    online_users = list(routing_table.keys())
    offline_users = [u for u in all_users if u not in online_users]

    socketio.emit('update_users', {'online': online_users, 'offline': offline_users})

def cleanup_stale_users():
    now = time.time()
    stale = [u for u, t in user_presence.items() if now - t > 10]
    for username in stale:
        if username in routing_table:
            del routing_table[username]
            del user_presence[username]
            for known_user, known_sid in routing_table.items():
                socketio.emit('receive_message', {'msg': f'{username} left the chat', 'type': 'system'}, to=known_sid)
            broadcast_users()
    threading.Timer(5, cleanup_stale_users).start()

cleanup_stale_users()

@app.route('/')
def root():
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if username:
            session['username'] = username
            return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('register')
def handle_register(username):
    routing_table[username] = request.sid
    user_presence[username] = time.time()

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

    all_users = get_all_users()
    online_users = list(routing_table.keys())
    offline_users = [u for u in all_users if u not in online_users]
    emit('update_users', {'online': online_users, 'offline': offline_users}, to=request.sid)

    emit('receive_message', {'msg': f'Welcome back, {username}!', 'type': 'system'}, to=request.sid)

    for known_user, known_sid in routing_table.items():
        if known_sid != request.sid:
            emit('receive_message', {'msg': f'{username} joined the chat', 'type': 'system'}, to=known_sid)

    broadcast_users()

@socketio.on('heartbeat')
def handle_heartbeat(data):
    username = data.get('username')
    if username:
        user_presence[username] = time.time()
        if username not in routing_table:
            routing_table[username] = request.sid
            broadcast_users()

@socketio.on('disconnect')
def handle_disconnect(reason=None):
    disconnected_user = None
    for username, sid in list(routing_table.items()):
        if sid == request.sid:
            disconnected_user = username
            del routing_table[username]
            if username in user_presence:
                del user_presence[username]
            break

    if disconnected_user:
        for known_user, known_sid in list(routing_table.items()):
            emit('receive_message', {'msg': f'{disconnected_user} left the chat', 'type': 'system'}, to=known_sid)

        broadcast_users()

@socketio.on('send_message')
def handle_message(data):
    sender = data.get('from')
    recipient = data.get('to')
    msg = data.get('msg')
    time = data.get('time')
    date = data.get('date')

    if not recipient:
        emit('receive_message', {'msg': 'Select a conversation first.', 'type': 'system'}, to=request.sid)
        return

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, recipient, message, timestamp, date, status) VALUES (?, ?, ?, ?, ?, 'sent')",
              (sender, recipient, msg, time, date))
    conn.commit()
    conn.close()

    if recipient in routing_table:
        recipient_sid = routing_table[recipient]
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
    c.execute('''SELECT sender, message, timestamp, status, date FROM messages
                 WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?)
                 ORDER BY id ASC''', (user1, user2, user2, user1))
    history = c.fetchall()
    conn.close()

    emit('load_history', {'history': history}, to=request.sid)

@socketio.on('delete_chat')
def handle_delete_chat(data):
    user1 = data.get('myName')
    user2 = data.get('theirName')

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?)",
              (user1, user2, user2, user1))
    conn.commit()
    conn.close()

    emit('chat_deleted', {'success': True}, to=request.sid)

    if user2 in routing_table:
        emit('chat_deleted_remote', {'deleted_by': user1}, to=routing_table[user2])

@socketio.on('clear_unread')
def handle_clear_unread(data):
    sender = data.get('sender')
    recipient = data.get('recipient')

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("UPDATE messages SET status='read' WHERE sender=? AND recipient=? AND status='sent'", (sender, recipient))
    conn.commit()
    conn.close()

    if sender in routing_table:
        emit('unread_counts', {'counts': {recipient: 0}}, to=routing_table[sender])

@socketio.on('get_unread_counts')
def handle_unread_counts(data):
    my_name = data.get('myName')

    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''SELECT sender, COUNT(*) FROM messages
                 WHERE recipient=? AND status='sent'
                 GROUP BY sender''', (my_name,))
    unread = {row[0]: row[1] for row in c.fetchall()}
    conn.close()

    emit('unread_counts', {'counts': unread}, to=request.sid)

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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

