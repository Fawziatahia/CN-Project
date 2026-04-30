function registerUser() {
    const myName = getMyName();
    if (myName !== "") {
        App.socket.emit('register', myName);
        const inp = document.getElementById('myName');
        inp.disabled = true;
        inp.classList.add('registered');
    }
}

function openChat(userName) {
    App.currentRecipient = userName;
    App.currentChatDate = "";

    const initial = userName.charAt(0).toUpperCase();
    const headerAvatar = document.getElementById('headerAvatar');
    headerAvatar.innerText = initial;
    headerAvatar.style.display = "flex";
    document.getElementById('headerAt').style.display = "inline-block";
    document.getElementById('activeChatName').innerText = userName;
    document.getElementById('closeChatBtn').style.display = "inline-flex";

    document.querySelectorAll('.user-item').forEach(el => el.classList.remove('active'));
    const target = document.querySelector(`.user-item[data-username="${userName}"]`);
    if (target) target.classList.add('active');

    document.getElementById('chat-box').innerHTML =
        `<div class="system-notification">Loading secure chat with ${userName}…</div>`;

    const myName = getMyName();
    App.socket.emit('get_history', { me: myName, them: userName });
    App.socket.emit('mark_read', { sender: userName, recipient: myName });
    App.socket.emit('clear_unread', { sender: userName, recipient: myName });

    const badge = document.querySelector(`.unread-badge[data-user="${userName}"]`);
    if (badge) badge.style.display = 'none';

    document.getElementById('messageInput').disabled = false;
    document.getElementById('messageInput').placeholder = "Type a message…";
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('emojiBtn').disabled = false;
}

function closeChat() {
    App.currentRecipient = "";
    App.currentChatDate = "";

    document.getElementById('headerAvatar').style.display = "none";
    document.getElementById('headerAt').style.display = "none";
    document.getElementById('activeChatName').innerText = "Pick a friend from the sidebar to start chatting";
    document.getElementById('closeChatBtn').style.display = "none";

    document.querySelectorAll('.user-item').forEach(el => el.classList.remove('active'));

    document.getElementById('chat-box').innerHTML = `
        <div class="welcome-state">
            <div class="welcome-icon"><i class="fa-regular fa-comments"></i></div>
            <h1 class="welcome-title">Welcome to Unicast</h1>
            <p class="welcome-sub">Choose someone from the left panel to begin.</p>
            <div class="welcome-arrow">
                <i class="fa-solid fa-arrow-left"></i>
            </div>
        </div>`;

    document.getElementById('messageInput').disabled = true;
    document.getElementById('messageInput').placeholder = "Select a conversation to start typing…";
    document.getElementById('sendBtn').disabled = true;
    document.getElementById('emojiBtn').disabled = true;

    const indicator = document.getElementById('typingIndicator');
    indicator.style.display = "none";
}

function deleteChat(userName) {
    if (!confirm(`Delete all messages with ${userName}? This can't be undone.`)) return;

    const myName = getMyName();
    closeAllUserMenus();
    App.socket.emit('delete_chat', { myName, theirName: userName });
}

function toggleUserMenu(event, userName) {
    event.stopPropagation();
    const menu = document.getElementById(`menu-${userName}`);
    const isOpen = menu.style.display === 'block';
    closeAllUserMenus();
    if (!isOpen) {
        menu.style.display = 'block';
    }
}

function closeAllUserMenus() {
    document.querySelectorAll('.user-menu-dropdown').forEach(m => m.style.display = 'none');
}

document.addEventListener('click', closeAllUserMenus);

App.socket.on('update_users', function(data) {
    const userListDiv = document.getElementById('userList');
    userListDiv.innerHTML = '';
    const myName = getMyName();
    let hasOtherUsers = false;

    const buildItem = (user, isOnline) => {
        const initial = user.charAt(0).toUpperCase();
        const dotClass = isOnline ? 'online' : 'offline';
        const offlineClass = isOnline ? '' : 'offline';
        const statusText = isOnline ? 'Online' : 'Offline';
        return `
            <div class="user-item ${offlineClass}" data-username="${user}" onclick="openChat('${user}')">
                <div class="avatar-wrap">
                    <div class="avatar">${initial}</div>
                    <span class="online-dot ${dotClass}"></span>
                </div>
                <div class="user-info">
                    <div class="user-name">${user}</div>
                    <div class="user-status">${statusText}</div>
                </div>
                <span class="unread-badge" data-user="${user}" style="display:none;"></span>
                <button class="user-menu-btn" title="More options" onclick="event.stopPropagation(); toggleUserMenu(event, '${user}')">
                    <i class="fa-solid fa-ellipsis-vertical"></i>
                </button>
                <div class="user-menu-dropdown" id="menu-${user}" style="display:none;">
                    <button class="user-menu-item delete-option" onclick="event.stopPropagation(); deleteChat('${user}')">
                        <i class="fa-solid fa-trash"></i> Delete chat
                    </button>
                </div>
            </div>`;
    };

    data.online.forEach(user => {
        if (user !== myName) {
            hasOtherUsers = true;
            userListDiv.innerHTML += buildItem(user, true);
        }
    });

    data.offline.forEach(user => {
        if (user !== myName) {
            hasOtherUsers = true;
            userListDiv.innerHTML += buildItem(user, false);
        }
    });

    if (!hasOtherUsers) {
        userListDiv.innerHTML = '<div class="user-item user-empty">No friends here yet</div>';
    }

    if (App.currentRecipient) {
        const target = document.querySelector(`.user-item[data-username="${App.currentRecipient}"]`);
        if (target) target.classList.add('active');
    }

    App.socket.emit('get_unread_counts', { myName });
});

App.socket.on('unread_counts', function(data) {
    document.querySelectorAll('.unread-badge').forEach(badge => {
        const user = badge.getAttribute('data-user');
        const count = data.counts[user] || 0;
        if (count > 0) {
            badge.textContent = count > 9 ? '9+' : count;
            badge.style.display = 'inline-flex';
        } else {
            badge.style.display = 'none';
        }
    });
});

App.socket.on('chat_deleted', function(data) {
    if (data.success) {
        closeChat();
        App.socket.emit('get_unread_counts', { myName: getMyName() });
    }
});
