from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import chess
import chess.engine
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Путь к Stockfish
engine_path = os.path.join(os.path.dirname(__file__), "stockfish.exe")

try:
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    logger.info("Stockfish engine started successfully")
except Exception as e:
    logger.error(f"Failed to start Stockfish: {e}")
    engine = None

# HTML шаблон с простой шахматной доской
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Шахматный Бот</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f0f0f0; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
        }
        .container { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            text-align: center; 
        }
        .chess-board { 
            display: inline-block; 
            border: 3px solid #8B4513; 
            margin: 20px 0; 
        }
        .row { 
            display: flex; 
        }
        .square { 
            width: 50px; 
            height: 50px; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            font-size: 35px; 
            cursor: pointer; 
            position: relative; 
        }
        .light { background-color: #f0d9b5; }
        .dark { background-color: #b58863; }
        .coordinates { 
            position: absolute; 
            font-size: 10px; 
            color: #000; 
        }
        .file-coord { bottom: 2px; right: 2px; }
        .rank-coord { top: 2px; left: 2px; }
        .selected { background-color: #aec6cf !important; }
        .possible-move { background-color: #90ee90 !important; }
        #status { 
            margin: 15px 0; 
            font-size: 18px; 
            font-weight: bold; 
            color: #333; 
        }
        button { 
            padding: 10px 20px; 
            background: #4CAF50; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 16px; 
            margin: 5px; 
        }
        button:hover { background: #45a049; }
        button:disabled { background: #cccccc; cursor: not-allowed; }
    </style>
</head>
<body>
    <div class="container">
        <h1>♞ Шахматный Бот ♞</h1>
        <div id="status">Ваш ход (белые)</div>
        <div class="chess-board" id="board">
            <!-- Доска будет сгенерирована JavaScript -->
        </div>
        <div>
            <button onclick="resetGame()">Новая игра</button>
            <button onclick="undoMove()">Отменить ход</button>
        </div>
        <div id="moves" style="margin-top: 15px; font-family: monospace;"></div>
    </div>

    <script>
        let gameState = {
            fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            selectedSquare: null,
            moves: []
        };

        // Юникод символы для фигур
        const pieceSymbols = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙'
        };

        // Создаем шахматную доску
        function createBoard() {
            const board = document.getElementById('board');
            board.innerHTML = '';
            
            const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
            const ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];
            
            for (let rankIdx = 0; rankIdx < 8; rankIdx++) {
                const row = document.createElement('div');
                row.className = 'row';
                
                for (let fileIdx = 0; fileIdx < 8; fileIdx++) {
                    const square = document.createElement('div');
                    const squareId = files[fileIdx] + ranks[rankIdx];
                    
                    // Определяем цвет клетки
                    square.className = `square ${(rankIdx + fileIdx) % 2 === 0 ? 'light' : 'dark'}`;
                    square.id = squareId;
                    
                    // Добавляем координаты
                    if (rankIdx === 7) {
                        const fileCoord = document.createElement('div');
                        fileCoord.className = 'coordinates file-coord';
                        fileCoord.textContent = files[fileIdx];
                        square.appendChild(fileCoord);
                    }
                    if (fileIdx === 0) {
                        const rankCoord = document.createElement('div');
                        rankCoord.className = 'coordinates rank-coord';
                        rankCoord.textContent = ranks[rankIdx];
                        square.appendChild(rankCoord);
                    }
                    
                    square.onclick = () => handleSquareClick(squareId);
                    row.appendChild(square);
                }
                board.appendChild(row);
            }
            
            updateBoard();
        }

        // Обновляем доску по FEN
        function updateBoard() {
            const board = chessBoardFromFen(gameState.fen);
            
            for (let rank = 0; rank < 8; rank++) {
                for (let file = 0; file < 8; file++) {
                    const squareId = String.fromCharCode(97 + file) + (8 - rank);
                    const square = document.getElementById(squareId);
                    const piece = board[rank][file];
                    
                    // Очищаем квадрат
                    square.innerHTML = '';
                    square.className = square.className.replace(' selected', '').replace(' possible-move', '');
                    
                    // Восстанавливаем координаты
                    if (rank === 7) {
                        const fileCoord = document.createElement('div');
                        fileCoord.className = 'coordinates file-coord';
                        fileCoord.textContent = String.fromCharCode(97 + file);
                        square.appendChild(fileCoord);
                    }
                    if (file === 0) {
                        const rankCoord = document.createElement('div');
                        rankCoord.className = 'coordinates rank-coord';
                        rankCoord.textContent = (8 - rank);
                        square.appendChild(rankCoord);
                    }
                    
                    // Добавляем фигуру
                    if (piece !== '.') {
                        const pieceElement = document.createElement('div');
                        pieceElement.textContent = pieceSymbols[piece] || piece;
                        pieceElement.style.cursor = 'pointer';
                        square.appendChild(pieceElement);
                    }
                    
                    // Восстанавливаем цвет
                    square.className = `square ${(rank + file) % 2 === 0 ? 'light' : 'dark'}`;
                }
            }
            
            // Подсвечиваем выбранную клетку
            if (gameState.selectedSquare) {
                const selected = document.getElementById(gameState.selectedSquare);
                if (selected) selected.className += ' selected';
            }
            
            updateStatus();
            updateMovesList();
        }

        // Парсим FEN в массив доски
        function chessBoardFromFen(fen) {
            const board = Array(8).fill().map(() => Array(8).fill('.'));
            const fenParts = fen.split(' ');
            const position = fenParts[0];
            let rank = 0, file = 0;
            
            for (let char of position) {
                if (char === '/') {
                    rank++;
                    file = 0;
                } else if (isNaN(char)) {
                    board[rank][file] = char;
                    file++;
                } else {
                    file += parseInt(char);
                }
            }
            return board;
        }

        // Обработка клика по клетке
        async function handleSquareClick(squareId) {
            if (!gameState.selectedSquare) {
                // Выбираем фигуру
                const board = chessBoardFromFen(gameState.fen);
                const file = squareId.charCodeAt(0) - 97;
                const rank = 8 - parseInt(squareId[1]);
                const piece = board[rank][file];
                
                if (piece !== '.' && piece === piece.toUpperCase()) { // Только белые фигуры
                    gameState.selectedSquare = squareId;
                    updateBoard();
                }
            } else {
                // Делаем ход
                const fromSquare = gameState.selectedSquare;
                const toSquare = squareId;
                
                try {
                    const response = await fetch('/move', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            from: fromSquare,
                            to: toSquare,
                            fen: gameState.fen
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        gameState.fen = data.newFen;
                        gameState.moves.push(`${fromSquare}-${toSquare}`);
                        
                        if (data.botMove) {
                            gameState.moves.push(`бот: ${data.botMove}`);
                        }
                    } else if (data.error) {
                        alert(data.error);
                    }
                    
                } catch (error) {
                    console.error('Ошибка:', error);
                    alert('Ошибка связи с сервером');
                }
                
                gameState.selectedSquare = null;
                updateBoard();
            }
        }

        // Обновляем статус игры
        function updateStatus() {
            const status = document.getElementById('status');
            const fenParts = gameState.fen.split(' ');
            const turn = fenParts[1];
            
            status.textContent = turn === 'w' ? 'Ваш ход (белые)' : 'Ход бота (чёрные)';
        }

        // Обновляем список ходов
        function updateMovesList() {
            const movesDiv = document.getElementById('moves');
            movesDiv.innerHTML = '<strong>Ходы:</strong><br>' + gameState.moves.join('<br>');
        }

        // Новая игра
        function resetGame() {
            gameState = {
                fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                selectedSquare: null,
                moves: []
            };
            updateBoard();
        }

        // Отменить ход
        function undoMove() {
            if (gameState.moves.length >= 2) {
                gameState.moves.pop(); // Ход бота
                gameState.moves.pop(); // Наш ход
                // Здесь можно добавить логику для отмены хода на сервере
                alert('Функция отмены хода в разработке');
            }
        }

        // Инициализация при загрузке страницы
        document.addEventListener('DOMContentLoaded', createBoard);
    </script>
</body>
</html>
'''

@app.route("/")
def index():
    return HTML_TEMPLATE

@app.route("/move", methods=["POST"])
def move():
    if not engine:
        return jsonify({"error": "Chess engine not available"}), 500
        
    try:
        data = request.get_json()
        from_square = data.get("from")
        to_square = data.get("to")
        fen = data.get("fen")
        
        # Создаем доску из FEN
        board = chess.Board(fen)
        
        # Пробуем сделать ход
        move = chess.Move.from_uci(f"{from_square}{to_square}")
        
        if move in board.legal_moves:
            board.push(move)
            
            # Ход бота
            bot_move = None
            if not board.is_game_over():
                result = engine.play(board, chess.engine.Limit(time=0.5))
                bot_move = board.san(result.move)
                board.push(result.move)
            
            return jsonify({
                "success": True,
                "newFen": board.fen(),
                "botMove": bot_move,
                "gameOver": board.is_game_over(),
                "result": board.result() if board.is_game_over() else "*"
            })
        else:
            return jsonify({"success": False, "error": "Некорректный ход"})
            
    except Exception as e:
        logger.error(f"Error in /move: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)