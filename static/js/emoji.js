const PASTEL_EMOJIS = [
    '😀','😃','😄','😁','😆','😅','😂','🤣','😊','😇',
    '🙂','🙃','😉','😌','😍','🥰','😘','😗','😙','😚',
    '😋','😛','😝','😜','🤪','🤨','🧐','🤓','😎','🤩',
    '🥳','😏','😒','😞','😔','😟','😕','🙁','😣','😢',
    '😭','😤','😠','😡','🤬','🤯','😳','🥵','🥶','😱',
    '😨','😰','😥','😓','🤗','🤔','🤭','🤫','🤥','😴',
    '👍','👎','👌','✌️','🤞','🤟','🤘','👏','🙌','👋',
    '🤝','🙏','💪','🔥','✨','⭐','🎉','🎊','🎁','💯',
    '❤️','💔','💕','💖','💗','💜','💛','💚','💙','🤍',
    '🌸','🌺','🌷','🌹','🌻','🌼','🍀','🌿','🌈','☀️',
    '🌙','⚡','☕','🍰','🍩','🍪','🍕','🍔','🍦','🍓'
];

function insertAtCursor(el, text) {
    const start = el.selectionStart || 0;
    const end = el.selectionEnd || 0;
    el.value = el.value.slice(0, start) + text + el.value.slice(end);
    el.selectionStart = el.selectionEnd = start + text.length;

    el.dispatchEvent(new Event('input', { bubbles: true }));
}

function initEmojiPicker() {
    const btn = document.getElementById('emojiBtn');
    const panel = document.getElementById('emojiPanel');
    const input = document.getElementById('messageInput');

    if (!btn || !panel || !input) return;

    panel.innerHTML = PASTEL_EMOJIS
        .map(e => `<button type="button" class="emoji-cell">${e}</button>`)
        .join('');

    btn.addEventListener('click', function(e) {
        e.stopPropagation();
        panel.classList.toggle('open');
    });

    panel.addEventListener('click', function(e) {
        const cell = e.target.closest('.emoji-cell');
        if (cell) {
            insertAtCursor(input, cell.textContent);
            input.focus();
        }
    });

    document.addEventListener('click', function(e) {
        if (panel.classList.contains('open') &&
            !panel.contains(e.target) &&
            e.target !== btn && !btn.contains(e.target)) {
            panel.classList.remove('open');
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && panel.classList.contains('open')) {
            panel.classList.remove('open');
        }
    });
}

initEmojiPicker();
