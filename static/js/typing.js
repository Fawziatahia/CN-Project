function bindTypingHandlers() {
    const input = document.getElementById('messageInput');

    input.addEventListener('input', function() {
        const myName = getMyName();
        if (myName !== "" && App.currentRecipient !== "") {
            App.socket.emit('typing', { from: myName, to: App.currentRecipient });
            clearTimeout(App.typingTimeout);
            App.typingTimeout = setTimeout(function() {
                App.socket.emit('stop_typing', { to: App.currentRecipient });
            }, 10000);
        }
    });
}

App.socket.on('is_typing', function(data) {
    if (!App.currentRecipient || data.sender !== App.currentRecipient) return;
    const indicator = document.getElementById('typingIndicator');
    indicator.innerHTML =
        `<span class="typing-dots"><span></span><span></span><span></span></span> <strong>${data.sender}</strong> is typing…`;
    indicator.style.display = "flex";
});

App.socket.on('stopped_typing', function() {
    if (!App.currentRecipient) return;
    const indicator = document.getElementById('typingIndicator');
    indicator.style.display = "none";
});
