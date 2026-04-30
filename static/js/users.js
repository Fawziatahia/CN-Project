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

    document.querySelectorAll('.user-item').forEach(el => el.classList.remove('active'));
    const target = document.querySelector(`.user-item[data-username="${userName}"]`);
    if (target) target.classList.add('active');

    document.getElementById('chat-box').innerHTML =
        `<div class="system-notification">Loading secure chat with ${userName}…</div>`;

    const myName = getMyName();
    App.socket.emit('get_history', { me: myName, them: userName });
    App.socket.emit('mark_read', { sender: userName, recipient: myName });
}

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
});
