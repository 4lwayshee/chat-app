from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import json
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

USERS = {
    'test': 'test',
    'test2': 'test2',
    'test3': 'test3',
    'test4': 'test4'
}
HISTORY_DIR = 'chat-history'
DB_PATH = 'chat.db'

# 폴더가 없으면 생성
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  room_id TEXT,
                  sender TEXT,
                  text TEXT,
                  time TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS read_status
                 (username TEXT,
                  room_id TEXT,
                  last_read INTEGER,
                  PRIMARY KEY (username, room_id))''')
    conn.commit()
    conn.close()

init_db()

def get_user_file(username, room_id):
    if room_id == 'group':
        return os.path.join(HISTORY_DIR, 'group.json')
    else:
        # 1:1 채팅은 두 사용자 이름을 정렬해서 같은 파일 사용
        users = sorted([username, room_id])
        return os.path.join(HISTORY_DIR, f'{users[0]}_{users[1]}.json')

def load_messages(username, room_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT sender, text, time FROM messages WHERE room_id = ? ORDER BY id', (room_id,))
    rows = c.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        messages.append({
            'sender': row[0],
            'text': row[1],
            'time': row[2]
        })
    return messages

def get_unread_count(username, room_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT last_read FROM read_status WHERE username = ? AND room_id = ?', (username, room_id))
    result = c.fetchone()
    last_read = result[0] if result else 0
    
    c.execute('SELECT COUNT(*) FROM messages WHERE room_id = ? AND sender != ? AND id > ?', (room_id, username, last_read))
    unread = c.fetchone()[0]
    
    conn.close()
    return unread

def mark_as_read(username, room_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT MAX(id) FROM messages WHERE room_id = ?', (room_id,))
    result = c.fetchone()
    max_id = result[0] if result[0] else 0
    
    c.execute('INSERT OR REPLACE INTO read_status (username, room_id, last_read) VALUES (?, ?, ?)',
              (username, room_id, max_id))
    
    conn.commit()
    conn.close()

def save_message(room_id, sender, text, time):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO messages (room_id, sender, text, time) VALUES (?, ?, ?, ?)',
              (room_id, sender, text, time))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'username' not in session:
        return render_template('secret.html')
    return redirect(url_for('rooms'))

@app.route('/rooms')
def rooms():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = session['username']
    other_users = [u for u in USERS.keys() if u != current_user]
    
    # 각 채팅방의 안읽은 메시지 수 계산
    unread_counts = {}
    unread_counts['group'] = get_unread_count(current_user, 'group')
    for user in other_users:
        unread_counts[user] = get_unread_count(current_user, user)
    
    return render_template('rooms.html', users=other_users, unread_counts=unread_counts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username in USERS and USERS[username] == password:
        session['username'] = username
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/chat/<room_id>')
def chat(room_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # 채팅방 입장 시 읽음 처리
    mark_as_read(session['username'], room_id)
    
    return render_template('index.html', room_id=room_id)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/send', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    data = request.json
    room_id = data.get('room_id')
    
    message = {
        'text': data['text'],
        'time': datetime.now().strftime('%H:%M'),
        'sender': username
    }
    
    save_message(room_id, username, message['text'], message['time'])
    
    return jsonify(message)

@app.route('/messages/<room_id>', methods=['GET'])
def get_messages(room_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    messages = load_messages(username, room_id)
    
    # 각 메시지에 isMine 플래그 추가
    for msg in messages:
        msg['isMine'] = msg.get('sender') == username
    
    return jsonify(messages)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
