import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Хранилище данных в памяти сервера
db_data = {
    "houses": [],
    "businesses": []
}

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Arizona RP Parser API is running"}), 200

@app.route('/api/update', methods=['POST'])
def update_data():
    """Принимает JSON от Lua-скрипта"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "No JSON provided"}), 400

    category = data.get("type") # 'houses' или 'businesses'
    items = data.get("items", []) # список объектов

    if category in db_data:
        db_data[category] = items
        return jsonify({"status": "success", "count": len(items)}), 200
    
    return jsonify({"status": "error", "message": "Invalid category type"}), 400

@app.route('/api/get', methods=['GET'])
def get_data():
    """Возвращает сохранённый список домов или бизнесов"""
    category = request.args.get('type', 'houses')
    return jsonify({
        "status": "success",
        "type": category,
        "items": db_data.get(category, [])
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)