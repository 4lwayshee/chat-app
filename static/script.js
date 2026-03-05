const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const roomTitle = document.getElementById('roomTitle');

if (roomId === 'group') {
    roomTitle.textContent = '전체 채팅방';
} else {
    roomTitle.textContent = roomId;
}

function loadMessages() {
    fetch(`/messages/${roomId}`)
        .then(res => res.json())
        .then(messages => {
            console.log('Loaded messages:', messages);
            chatMessages.innerHTML = '';
            messages.forEach(msg => displayMessage(msg));
        });
}

function displayMessage(msg) {
    const messageDiv = document.createElement('div');
    messageDiv.className = msg.isMine ? 'message mine' : 'message theirs';
    
    let senderHtml = '';
    if (!msg.isMine && msg.sender) {
        senderHtml = `<div class="message-sender">${msg.sender}</div>`;
    }
    
    messageDiv.innerHTML = `
        ${senderHtml}
        <div class="message-bubble">${msg.text}</div>
        <div class="message-time">${msg.time}</div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    fetch('/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text, room_id: roomId})
    })
    .then(res => res.json())
    .then(msg => {
        msg.isMine = true;
        displayMessage(msg);
        messageInput.value = '';
    });
}

sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

loadMessages();
