import argparse
import json
import statistics
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

BASE = "http://localhost:8080"


def set_algorithm(name):
    req = urllib.request.Request(
        BASE + "/algorithm",
        data=json.dumps({"algorithm": name}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=5).read()


def one_request(path):
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(BASE + path, timeout=15) as resp:
            body = json.loads(resp.read())
        return body.get("servidor", "?"), time.perf_counter() - start
    except Exception:
        return "ERRO", time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser(description="Teste de carga ShopNow")
    parser.add_argument("--algorithm", default="round_robin",
                        choices=["round_robin", "least_connections"])
    parser.add_argument("--requests", type=int, default=300)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--path", default="/")
    args = parser.parse_args()

    set_algorithm(args.algorithm)
    print(f"Algoritmo: {args.algorithm} | Requisicoes: {args.requests} "
          f"| Concorrencia: {args.concurrency} | Rota: {args.path}")

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(one_request, [args.path] * args.requests))
    total = time.perf_counter() - start

    counts = Counter(server for server, _ in results)
    latencies = sorted(t for server, t in results if server != "ERRO")

    print("\nDistribuicao por servidor:")
    for server in sorted(counts):
        pct = counts[server] / args.requests * 100
        print(f"  {server}: {counts[server]} ({pct:.1f}%)")

    if latencies:
        p95 = latencies[int(len(latencies) * 0.95) - 1]
        print(f"\nTempo total: {total:.2f}s")
        print(f"Throughput: {args.requests / total:.1f} req/s")
        print(f"Latencia media: {statistics.mean(latencies) * 1000:.1f} ms")
        print(f"Latencia p95: {p95 * 1000:.1f} ms")

    print(f"Erros: {counts.get('ERRO', 0)}")


if __name__ == "__main__":
    main()