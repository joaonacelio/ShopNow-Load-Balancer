from flask import Flask, jsonify, request
import os
import time

app = Flask(__name__)

# Identifica qual instancia esta executando
SERVER_ID = os.getenv("SERVER_ID", "Servidor Local")


@app.route("/")
def home():
    return jsonify({
        "projeto": "ShopNow",
        "mensagem": "Servidor funcionando!",
        "servidor": SERVER_ID,
        "status": "online"
    })


@app.route("/health")
def health():
    return jsonify({
        "servidor": SERVER_ID,
        "status": "online"
    })


@app.route("/slow")
def slow():
    # Simula uma requisicao demorada (usada para testar Least Connections)
    try:
        seconds = float(request.args.get("seconds", 5))
    except ValueError:
        seconds = 5

    seconds = max(0, min(seconds, 30))
    time.sleep(seconds)

    return jsonify({
        "projeto": "ShopNow",
        "mensagem": "Resposta lenta concluida",
        "servidor": SERVER_ID,
        "segundos": seconds
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)