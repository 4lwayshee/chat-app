from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import json
import os
import pytz

try:
    import psycopg2
    from urllib.parse import urlparse
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

USERS = {
    'hee': 'q1',
    'sen': 'q1',
    'test3': 'test3',
    'test4': 'test4'
}
# 데이터베이스 연결
def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if database_url and PSYCOPG2_AVAILABLE:
        # PostgreSQL (Render)
        return psycopg2.connect(database_url)
    else:
        # 로컬에서는 JSON 파일 사용
        return None

# 데이터베이스 초기화
def init_db():
    conn = get_db_connection()
    if conn and PSYCOPG2_AVAILABLE:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                room_id TEXT,
                sender TEXT,
                text TEXT,
                time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS read_status (
                username TEXT,
                room_id TEXT,
                last_read INTEGER,
                PRIMARY KEY (username, room_id)
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
    else:
        # 로컬에서는 폴더 생성
        if not os.path.exists(HISTORY_DIR):
            os.makedirs(HISTORY_DIR)

HISTORY_DIR = 'chat-history'

def get_user_file(username, room_id):
    if room_id == 'group':
        return os.path.join(HISTORY_DIR, 'group.json')
    else:
        users = sorted([username, room_id])
        return os.path.join(HISTORY_DIR, f'{users[0]}_{users[1]}.json')

def save_messages(username, room_id, messages):
    user_file = get_user_file(username, room_id)
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

init_db()

def get_user_file(username, room_id):
    if room_id == 'group':
        return os.path.join(HISTORY_DIR, 'group.json')
    else:
        users = sorted([username, room_id])
        return os.path.join(HISTORY_DIR, f'{users[0]}_{users[1]}.json')

def load_messages(username, room_id):
    conn = get_db_connection()
    if conn:
        # PostgreSQL 사용
        cur = conn.cursor()
        cur.execute('SELECT sender, text, time FROM messages WHERE room_id = %s ORDER BY id', (room_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        messages = []
        for row in rows:
            messages.append({
                'sender': row[0],
                'text': row[1],
                'time': row[2]
            })
        return messages
    else:
        # 로컬에서는 JSON 파일 사용
        user_file = get_user_file(username, room_id)
        if os.path.exists(user_file):
            with open(user_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

def get_unread_count(username, room_id):
    messages = load_messages(username, room_id)
    read_file = os.path.join(HISTORY_DIR, f'{username}_read.json')
    
    read_data = {}
    if os.path.exists(read_file):
        with open(read_file, 'r', encoding='utf-8') as f:
            read_data = json.load(f)
    
    last_read = read_data.get(room_id, 0)
    unread = 0
    
    for msg in messages:
        if msg.get('sender') != username:
            msg_index = messages.index(msg)
            if msg_index >= last_read:
                unread += 1
    
    return unread

def mark_as_read(username, room_id):
    messages = load_messages(username, room_id)
    read_file = os.path.join(HISTORY_DIR, f'{username}_read.json')
    
    read_data = {}
    if os.path.exists(read_file):
        with open(read_file, 'r', encoding='utf-8') as f:
            read_data = json.load(f)
    
    read_data[room_id] = len(messages)
    
    with open(read_file, 'w', encoding='utf-8') as f:
        json.dump(read_data, f, ensure_ascii=False, indent=2)

def save_message(room_id, sender, text, time):
    conn = get_db_connection()
    if conn:
        # PostgreSQL 사용
        cur = conn.cursor()
        cur.execute('INSERT INTO messages (room_id, sender, text, time) VALUES (%s, %s, %s, %s)',
                   (room_id, sender, text, time))
        conn.commit()
        cur.close()
        conn.close()
    else:
        # 로컬에서는 JSON 파일 사용
        messages = load_messages(sender, room_id)
        message = {'text': text, 'time': time, 'sender': sender}
        messages.append(message)
        save_messages(sender, room_id, messages)

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
    
    # 한국 시간으로 변환
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    
    message = {
        'text': data['text'],
        'time': now.strftime('%H:%M'),
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
