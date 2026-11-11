from flask import Flask, request, jsonify, Response
from concurrent.futures import ThreadPoolExecutor
import requests
import threading
import time

app = Flask(__name__)

# Servidores disponiveis
SERVERS = [
    {"name": "Servidor 1", "url": "http://servidor1:5000", "active": 0, "healthy": True},
    {"name": "Servidor 2", "url": "http://servidor2:5000", "active": 0, "healthy": True},
    {"name": "Servidor 3", "url": "http://servidor3:5000", "active": 0, "healthy": True},
]

# Configuracoes
HEALTH_INTERVAL = 3   # segundos entre verificacoes
HEALTH_TIMEOUT = 1    # timeout de cada verificacao
algorithm = "round_robin"
current_index = 0
lock = threading.Lock()


def check_health(server):
    try:
        response = requests.get(server["url"] + "/health", timeout=HEALTH_TIMEOUT)
        return response.status_code == 200
    except requests.RequestException:
        return False


def health_loop():
    # Verifica todos os servidores em paralelo e guarda o resultado
    with ThreadPoolExecutor(max_workers=len(SERVERS)) as pool:
        while True:
            results = list(pool.map(check_health, SERVERS))
            with lock:
                for server, ok in zip(SERVERS, results):
                    server["healthy"] = ok
            time.sleep(HEALTH_INTERVAL)


def select_server(excluded):
    global current_index

    with lock:
        candidates = [
            s for s in SERVERS
            if s["healthy"] and s["name"] not in excluded
        ]

        if not candidates:
            return None

        if algorithm == "least_connections":
            selected = min(candidates, key=lambda s: s["active"])
        else:
            selected = candidates[current_index % len(candidates)]
            current_index += 1

        selected["active"] += 1

    return selected


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def balance(path):
    tried = set()

    # Tenta ate um servidor diferente por vez (tolerancia a falhas)
    for _ in range(len(SERVERS)):
        server = select_server(tried)

        if server is None:
            break

        tried.add(server["name"])

        try:
            response = requests.request(
                method=request.method,
                url=server["url"] + "/" + path,
                params=request.args,
                data=request.get_data(),
                headers={
                    key: value
                    for key, value in request.headers
                    if key.lower() not in ["host", "content-length", "connection"]
                },
                timeout=10
            )

            excluded_headers = [
                "content-encoding", "content-length",
                "transfer-encoding", "connection"
            ]

            headers = [
                (key, value)
                for key, value in response.headers.items()
                if key.lower() not in excluded_headers
            ]

            return Response(response.content, status=response.status_code, headers=headers)

        except requests.RequestException:
            # Marca como fora do ar na hora; o health check recupera depois
            with lock:
                server["healthy"] = False

        finally:
            with lock:
                server["active"] -= 1

    return jsonify({"erro": "Nenhum servidor disponível!"}), 503


@app.route("/algorithm", methods=["GET", "POST"])
def change_algorithm():
    global algorithm

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        new_algorithm = data.get("algorithm", "").lower()

        if new_algorithm not in ["round_robin", "least_connections"]:
            return jsonify({"erro": "Algoritmo inválido!"}), 400

        with lock:
            algorithm = new_algorithm

        return jsonify({
            "mensagem": "Algoritmo alterado com sucesso!",
            "algorithm": algorithm
        })

    return jsonify({"algorithm": algorithm})


@app.route("/stats")
def stats():
    with lock:
        return jsonify({
            "algorithm": algorithm,
            "servers": [
                {
                    "name": s["name"],
                    "active_connections": s["active"],
                    "healthy": s["healthy"]
                }
                for s in SERVERS
            ]
        })


@app.route("/health")
def health():
    return jsonify({"status": "online", "service": "ShopNow Load Balancer"})


# Inicia o health check em segundo plano
threading.Thread(target=health_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)