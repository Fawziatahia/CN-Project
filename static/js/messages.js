function sendMessage() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();
    const myName = getMyName();

    if (text !== "" && App.currentRecipient !== "") {
        const box = document.getElementById('chat-box');
        clearWelcomeState();

        const time = getTimeString();
        const date = getDateString();

        if (date !== App.currentChatDate) {
            box.innerHTML += `<div class="date-divider"><span>Today</span></div>`;
            App.currentChatDate = date;
        }

        box.innerHTML += `
            <div class="message-group my-message">
                <div class="msg sent">${text}</div>
                <span class="timestamp-out">${time} <span class="read-ticks ticks-sent">${App.checkmarkSVG}</span></span>
            </div>`;
        scrollChatToBottom();

        App.socket.emit('send_message', { from: myName, to: App.currentRecipient, msg: text, time: time, date: date });
        input.value = "";

        clearTimeout(App.typingTimeout);
        App.socket.emit('stop_typing', { to: App.currentRecipient });
    } else if (App.currentRecipient === "") {
        alert("Please click a user in the sidebar to start chatting!");
    }
}

App.socket.on('load_history', function(data) {
    const box = document.getElementById('chat-box');
    box.innerHTML = '';
    const myName = getMyName();

    if (data.history.length === 0) {
        box.innerHTML = `<div class="system-notification">This is the start of your chat history.</div>`;
        return;
    }

    data.history.forEach(row => {
        const sender = row[0];
        const msg = row[1];
        const time = row[2];
        const status = row[3];
        const date = row[4] || getDateString();

        if (date !== App.currentChatDate) {
            const displayDate = (date === getDateString()) ? "Today" : date;
            box.innerHTML += `<div class="date-divider"><span>${displayDate}</span></div>`;
            App.currentChatDate = date;
        }

        if (sender === myName) {
            const tickClass = status === 'read' ? 'ticks-read' : 'ticks-sent';
            box.innerHTML += `
                <div class="message-group my-message">
                    <div class="msg sent">${msg}</div>
                    <span class="timestamp-out">${time} <span class="read-ticks ${tickClass}">${App.checkmarkSVG}</span></span>
                </div>`;
        } else {
            box.innerHTML += `
                <div class="message-group their-message">
                    <div class="msg received">${msg}</div>
                    <span class="timestamp-out">${time}</span>
                </div>`;
        }
    });
    scrollChatToBottom();
});

App.socket.on('receive_message', function(data) {
    const box = document.getElementById('chat-box');
    const time = data.timestamp || getTimeString();
    const date = data.date || getDateString();
    const myName = getMyName();

    if (data.type === 'system') {
        box.innerHTML += `<div class="system-notification">${data.msg} • ${time}</div>`;
        scrollChatToBottom();
    } else {
        if (data.sender === App.currentRecipient) {
            clearWelcomeState();

            if (date !== App.currentChatDate) {
                const displayDate = (date === getDateString()) ? "Today" : date;
                box.innerHTML += `<div class="date-divider"><span>${displayDate}</span></div>`;
                App.currentChatDate = date;
            }

            box.innerHTML += `
                <div class="message-group their-message">
                    <div class="msg received">${data.msg}</div>
                    <span class="timestamp-out">${time}</span>
                </div>`;
            scrollChatToBottom();

            App.socket.emit('mark_read', { sender: data.sender, recipient: myName });
        }
    }
});

App.socket.on('messages_read', function(data) {
    if (data.reader === App.currentRecipient) {
        document.querySelectorAll('.ticks-sent').forEach(tick => {
            tick.classList.remove('ticks-sent');
            tick.classList.add('ticks-read');
        });
    }
});
