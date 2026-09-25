import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

SECRET_KEY = "usefguIHSFUSDFGUjhjfk88448"  # Ключ из вашего property_tracker.lua
DB_FILE = "tracker.db"

# Инициализация структуры БД
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Таблица для хранения текущей недвижимости
    c.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server TEXT NOT NULL,
            prop_type TEXT NOT NULL,
            prop_id INTEGER,
            payday INTEGER NOT NULL,
            position INTEGER NOT NULL,
            scanner TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(server, prop_type, position) ON CONFLICT REPLACE
        )
    ''')
    # Таблица для логов сканирования (Консоль / Сканы)
    c.execute('''
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server TEXT NOT NULL,
            scanner TEXT NOT NULL,
            count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- API ДЛЯ LUA-СКРИПТА ---

@app.route('/update', methods=['POST'])
def update_data():
    """Принимает батч данных от property_tracker.lua"""
    # Проверка секретного ключа из заголовка X-Secret-Key
    client_key = request.headers.get("X-Secret-Key")
    if client_key != SECRET_KEY:
        return jsonify({"status": "error", "message": "Unauthorized: invalid secret key"}), 403

    data = request.get_json(silent=True)
    if not data or "server" not in data or "entries" not in data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    server = data["server"]
    scanner = data.get("scanner", "unknown")
    entries = data["entries"]

    if not entries:
        return jsonify({"status": "success", "message": "No entries to process"}), 200

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Очищаем старые записи для данного типа недвижимости перед обновлением позиции
    prop_types_in_batch = set(e.get("propType") for e in entries if e.get("propType"))
    for p_type in prop_types_in_batch:
        c.execute("DELETE FROM properties WHERE server = ? AND prop_type = ?", (server, p_type))

    # Записываем полученный список объектов
    for entry in entries:
        c.execute('''
            INSERT INTO properties (server, prop_type, prop_id, payday, position, scanner, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            server,
            entry.get("propType", "house"),
            entry.get("propId"),
            entry.get("pd", 0),
            entry.get("pos", 1),
            scanner,
            datetime.utcnow()
        ))

    # Фиксируем лог сканирования
    c.execute('INSERT INTO scan_logs (server, scanner, count) VALUES (?, ?, ?)',
              (server, scanner, len(entries)))

    conn.commit()
    conn.close()

    print(f"[Tracker] Успешно обновлено: {server} | Игрок: {scanner} | Объектов: {len(entries)}")
    return jsonify({"status": "success", "processed": len(entries)}), 200


@app.route('/time', methods=['GET'])
def get_time():
    """Эндпоинт синхранизации времени"""
    return jsonify({"timestamp": int(datetime.utcnow().timestamp())})


# --- ВЕБ-ИНТЕРФЕЙС (Панель в стиле игры) ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Arizona RP — Мониторинг недвижимости</title>
    <style>
        body {
            background-color: #0f0f11;
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .dialog-box {
            background: rgba(18, 18, 20, 0.95);
            border: 2px solid #333;
            border-radius: 8px;
            width: 520px;
            box-shadow: 0 0 20px rgba(0,0,0,0.8);
            padding: 15px;
        }
        .header {
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 12px;
            border-bottom: 1px solid #2a2a2e;
            padding-bottom: 8px;
        }
        .header .page-num { color: #55ff55; }
        .controls {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            gap: 10px;
        }
        select, button {
            background: #222226;
            color: #fff;
            border: 1px solid #444;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
        }
        select:focus, button:focus { outline: none; border-color: #666; }
        .table-header {
            display: flex;
            color: #888;
            font-size: 14px;
            padding: 4px 8px;
            border-bottom: 1px solid #333;
        }
        .col-num { width: 10%; }
        .col-info { width: 90%; text-align: center; }
        .list-container {
            max-height: 380px;
            overflow-y: auto;
            margin-bottom: 15px;
        }
        .row {
            display: flex;
            padding: 8px;
            font-size: 15px;
            border-bottom: 1px solid #1a1a1e;
        }
        .row:nth-child(even) { background: rgba(255,255,255,0.02); }
        .row.active {
            background: rgba(139, 0, 0, 0.35);
            border-left: 3px solid #ff4444;
        }
        .col-title { width: 55%; color: #ffffff; }
        .col-payday { width: 45%; text-align: right; }
        .pd-high { color: #ff5555; font-weight: bold; }
        .pd-normal { color: #ffffff; }
        .footer {
            display: flex;
            justify-content: center;
            gap: 15px;
        }
        .btn {
            background: #2a2a30;
            color: #fff;
            border: 1px solid #555;
            padding: 8px 24px;
            border-radius: 6px;
            font-weight: bold;
        }
        .btn:hover { background: #3a3a42; }
        .meta-info {
            font-size: 11px;
            color: #666;
            text-align: center;
            margin-top: 10px;
        }
    </style>
</head>
<body>

<div class="dialog-box">
    <div class="header">
        Страница №1 (<span class="page-num">{{ 'Дома' if prop_type == 'house' else 'Бизнесы' }}</span>)
    </div>

    <form method="GET" action="/" class="controls">
        <select name="server" onchange="this.form.submit()">
            {% for s in servers %}
                <option value="{{ s }}" {% if s == current_server %}selected{% endif %}> Сервер: {{ s }}</option>
            {% endfor %}
        </select>

        <select name="type" onchange="this.form.submit()">
            <option value="house" {% if prop_type == 'house' %}selected{% endif %}>Дома</option>
            <option value="business" {% if prop_type == 'business' %}selected{% endif %}>Бизнесы</option>
        </select>
    </form>

    <div class="table-header">
        <div class="col-num">№</div>
        <div class="col-info">Информация</div>
    </div>

    <div class="list-container">
        {% if items %}
            {% for item in items %}
            <div class="row {% if item.position == 1 %}active{% endif %}">
                <div class="col-num">{{ item.position }}.</div>
                <div class="col-title">
                    {% if item.prop_type == 'house' %}
                        Дом {% if item.prop_id %}(ID: {{ item.prop_id }}){% else %}(Неизвестно){% endif %}
                    {% else %}
                        Бизнес {% if item.prop_id %}(ID: {{ item.prop_id }}){% else %}(Неизвестно){% endif %}
                    {% endif %}
                </div>
                <div class="col-payday">
                    Слетит через: 
                    <span class="{% if item.payday <= 3 or item.payday >= 15 %}pd-high{% else %}pd-normal{% endif %}">
                        {{ item.payday }} Payday.
                    </span>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="row" style="justify-content: center; color: #777; padding: 20px;">
                Нет данных по выбранному серверу
            </div>
        {% endif %}
    </div>

    <div class="footer">
        <button class="btn">Далее</button>
        <button class="btn">Закрыть</button>
    </div>

    {% if items %}
    <div class="meta-info">
        Последнее сканирование: {{ items[0].updated_at }} | Сканер: {{ items[0].scanner }}
    </div>
    {% endif %}
</div>

</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    server = request.args.get('server', 'Phoenix')
    prop_type = request.args.get('type', 'house')

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Список всех сохранённых серверов
    c.execute('SELECT DISTINCT server FROM properties')
    servers = [row['server'] for row in c.fetchall()]
    if not servers:
        servers = ["Phoenix"]

    # Запрос актуального списка недвижимости
    c.execute('''
        SELECT position, prop_type, prop_id, payday, scanner, updated_at
        FROM properties
        WHERE server = ? AND prop_type = ?
        ORDER BY position ASC
    ''', (server, prop_type))
    
    items = [dict(row) for row in c.fetchall()]
    conn.close()

    return render_template_string(
        HTML_TEMPLATE,
        items=items,
        servers=servers,
        current_server=server,
        prop_type=prop_type
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
