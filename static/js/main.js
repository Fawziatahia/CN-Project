// Boot — wire up DOM events and auto-register the logged-in user.
document.getElementById('messageInput').addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

document.getElementById('sendBtn').addEventListener('click', sendMessage);

bindTypingHandlers();

// Username comes from the server-side session via the hidden #myName input.
const initialName = getMyName();
if (initialName) {
    App.socket.emit('register', initialName);
}
