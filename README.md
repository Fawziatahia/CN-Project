# Unicast

A real-time one-to-one chat app built with **Flask** + **Flask-SocketIO** + **SQLite**, featuring a fullscreen pastel glassmorphic frontend.

No passwords, no signup — pick a display name and start chatting.

---

## Features

- One-to-one (unicast) messaging over WebSockets
- Online / offline user list, broadcast on connect/disconnect
- Persistent chat history (SQLite)
- Read receipts (sent / read ticks)
- Typing indicator
- Date dividers in chat history
- Emoji picker (110+ emojis)
- Pastel glassmorphism UI, Questrial Google font
- Session-based name (no auth) — `/login` then `/chat`

---

## Tech stack

| Layer    | Tool                                |
| -------- | ----------------------------------- |
| Backend  | Python 3, Flask, Flask-SocketIO     |
| Storage  | SQLite (`chat.db`)                  |
| Realtime | Socket.IO (4.0.1) over WebSockets   |
| Frontend | Vanilla JS (modular), CSS, Jinja2   |
| Font     | [Questrial](https://fonts.google.com/specimen/Questrial) |
| Icons    | Font Awesome 6                      |

---

## Project structure

```
CN-Project/
├── app.py                       # Flask app + SocketIO handlers + routes
├── chat.db                      # SQLite database (auto-created)
├── README.md
├── static/
│   ├── style.css                # Pastel glassmorphism theme
│   └── js/
│       ├── state.js             # Shared App namespace (socket, state)
│       ├── utils.js             # Time/date/DOM helpers
│       ├── users.js             # registerUser, openChat, user list
│       ├── messages.js          # sendMessage, history, receive
│       ├── typing.js            # Typing indicator handlers
│       ├── emoji.js             # Emoji picker
│       └── main.js              # Boot + DOM event wiring
└── templates/
    ├── login.html               # /login — name picker card
    ├── index.html               # /chat — shell that includes partials
    └── partials/
        ├── sidebar.html         # User list + bottom user panel
        └── chat.html            # Header + messages + input + emoji
```

---

## Routes

| Method | Path      | Description                                      |
| ------ | --------- | ------------------------------------------------ |
| GET    | `/`       | Redirects to `/chat` if logged in, else `/login` |
| GET    | `/login`  | Renders the name-picker card                     |
| POST   | `/login`  | Saves the name to `session`, redirects to `/chat`|
| GET    | `/chat`   | The chat app (redirects to `/login` if no name)  |
| GET    | `/logout` | Clears the session                               |

---

## Socket.IO events

**Client → Server**
| Event          | Payload                                              |
| -------------- | ---------------------------------------------------- |
| `register`     | `username` (string)                                  |
| `send_message` | `{ from, to, msg, time, date }`                      |
| `get_history`  | `{ me, them }`                                       |
| `mark_read`    | `{ sender, recipient }`                              |
| `typing`       | `{ from, to }`                                       |
| `stop_typing`  | `{ to }`                                             |

**Server → Client**
| Event             | Payload                                              |
| ----------------- | ---------------------------------------------------- |
| `update_users`    | `{ online: [...], offline: [...] }`                  |
| `receive_message` | `{ msg, type, sender?, timestamp?, date? }`          |
| `load_history`    | `{ history: [[sender, msg, time, status, date]...] }`|
| `messages_read`   | `{ reader }`                                         |
| `is_typing`       | `{ sender }`                                         |
| `stopped_typing`  | —                                                    |

---

## Database schema

```sql
CREATE TABLE messages (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    sender    TEXT,
    recipient TEXT,
    message   TEXT,
    timestamp TEXT,
    date      TEXT,
    status    TEXT DEFAULT 'sent'   -- 'sent' | 'read'
);

CREATE TABLE users (
    username TEXT PRIMARY KEY
);
```

---

## Setup & run

### 1. Install dependencies

```bash
pip install flask flask-socketio
```

### 2. Run the server

```bash
python app.py
```

The app starts on `http://0.0.0.0:5000`.

### 3. Open in two browsers

Open two browser windows (or two devices on the same network) and visit:

```
http://127.0.0.1:5000/login
```

Pick a different name in each, and you'll see each other in the sidebar. Click a user to start a DM.

---

## Test it on a LAN

The server binds to `0.0.0.0`, so any device on the same Wi-Fi can reach it via your machine's local IP, e.g. `http://192.168.1.42:5000/login`.

Find your LAN IP:

- Windows: `ipconfig`
- macOS / Linux: `ifconfig` or `ip addr`

---

## Notes

- This is a learning / demo project — no real authentication, no message encryption, no password reset, etc. Don't expose `chat.db` or the server to the public internet.
- The Flask `secret_key` in `app.py` is hard-coded for development. Change it for any non-toy deployment.
- The `chat.db` file is created automatically on first run.
