from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

USERS = {
    'test': 'test',
    'test2': 'test2',
    'test3': 'test3',
    'test4': 'test4'
}
HISTORY_DIR = 'chat-history'

# 폴더가 없으면 생성
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def get_user_file(username, room_id):
    if room_id == 'group':
        return os.path.join(HISTORY_DIR, 'group.json')
    else:
        # 1:1 채팅은 두 사용자 이름을 정렬해서 같은 파일 사용
        users = sorted([username, room_id])
        return os.path.join(HISTORY_DIR, f'{users[0]}_{users[1]}.json')

def load_messages(username, room_id):
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

def save_messages(username, room_id, messages):
    user_file = get_user_file(username, room_id)
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
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
    
    messages = load_messages(username, room_id)
    
    message = {
        'text': data['text'],
        'time': datetime.now().strftime('%H:%M'),
        'sender': username
    }
    messages.append(message)
    save_messages(username, room_id, messages)
    return jsonify(message)

@app.route('/messages/<room_id>', methods=['GET'])
def get_messages(room_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    messages = load_messages(username, room_id)
    return jsonify(messages)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
