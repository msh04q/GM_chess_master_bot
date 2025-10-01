# GM_chess_master_bot

## 🚀 Запуск проект

2. **Скачайте Stockfish** и положите в `server/stockfish.exe`
3. **Скачайте ngrok.exe** и положите в `GM_chess_master_bot` корневая папка
4. **Запустите в Git Bash**: создание виртуального окружение в корневой папке и запуск
```bash
cd GM_chess_master_bot
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
cd server
python server.py
