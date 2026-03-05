# 배포 방법

## 1. 깃허브에 올리기

```bash
cd C:\chat-app
git init
git add .
git commit -m "Initial commit"
```

깃허브에서 새 repository 만들고:
```bash
git remote add origin https://github.com/YOUR_USERNAME/chat-app.git
git branch -M main
git push -u origin main
```

## 2. Render에 배포

1. https://render.com 접속 및 가입
2. "New +" 클릭 → "Web Service" 선택
3. 깃허브 연결 후 chat-app 저장소 선택
4. 설정:
   - Name: chat-app (원하는 이름)
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. "Create Web Service" 클릭

배포 완료 후 제공되는 URL로 접속 가능합니다!

## 주의사항

- 무료 플랜은 15분 미사용 시 슬립 모드
- 첫 접속 시 로딩 시간 소요
- 대화 이력은 서버 재시작 시 초기화될 수 있음 (영구 저장 필요 시 DB 사용)
