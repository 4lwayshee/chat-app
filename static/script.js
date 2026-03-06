const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');

// roomTitle 요소가 없으므로 제거

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

document.getElementById('heartBtn').addEventListener('click', () => {
    messageInput.value += '♥';
    messageInput.focus();
});

// 투명도 조절 기능
const opacitySlider = document.getElementById('opacitySlider');

// 저장된 투명도 값 불러오기
const savedOpacity = localStorage.getItem('chatOpacity') || '1';
opacitySlider.value = savedOpacity;
document.querySelector('.chat-container').style.opacity = savedOpacity;

opacitySlider.addEventListener('input', (e) => {
    const opacity = e.target.value;
    document.querySelector('.chat-container').style.opacity = opacity;
    // 투명도 값을 localStorage에 저장
    localStorage.setItem('chatOpacity', opacity);
});

loadMessages();

// 메세지 확인 주기 (필요시 아래 주석 해제)
// setInterval(() => {
//     loadMessages();
// }, 1500);
