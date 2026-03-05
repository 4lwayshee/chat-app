document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    const res = await fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    });
    
    const data = await res.json();
    
    if (data.success) {
        window.location.href = '/rooms';
    } else {
        document.getElementById('error').textContent = '아이디 또는 비밀번호가 잘못되었습니다.';
    }
});
