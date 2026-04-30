function getTimeString() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    return hours + ':' + minutes + ' ' + ampm;
}

function getDateString() {
    const now = new Date();
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return now.toLocaleDateString('en-US', options);
}

function getMyName() {
    return document.getElementById('myName').value.trim();
}

function scrollChatToBottom() {
    const box = document.getElementById('chat-box');
    box.scrollTop = box.scrollHeight;
}

function clearWelcomeState() {
    const w = document.querySelector('.welcome-state');
    if (w) w.remove();
}
