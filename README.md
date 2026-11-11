# ShopNow - Balanceador de Carga

Projeto acadêmico da disciplina de **Sistemas Distribuídos**.

**Autor:** João Nacélio Peixoto Santos

Sistema de balanceamento de carga desenvolvido com **Python**, **Flask** e **Docker**, com três servidores, dois algoritmos de distribuição, monitoramento por Health Check e tolerância a falhas.

## Funcionalidades

- **Round Robin:** distribui as requisições em rodízio entre os servidores saudáveis.
- **Least Connections:** envia cada requisição ao servidor com menos conexões ativas.
- **Health Check em segundo plano:** uma thread verifica os servidores a cada 3 segundos (timeout de 1 s) e guarda o resultado, sem atrasar as requisições.
- **Tolerância a falhas:** se um servidor falha durante uma requisição, ele é marcado como fora do ar e a requisição é reenviada a outro servidor. Se todos caírem, o balanceador responde `503`.
- **Troca de algoritmo em tempo real** e **estatísticas** por rotas HTTP.

## Arquitetura
cd "$HOME\OneDrive\Área de Trabalho\ShopNow"

@'
# ShopNow - Balanceador de Carga

Projeto acadêmico da disciplina de **Sistemas Distribuídos**.

**Autor:** João Nacélio Peixoto Santos

Sistema de balanceamento de carga desenvolvido com **Python**, **Flask** e **Docker**, com três servidores, dois algoritmos de distribuição, monitoramento por Health Check e tolerância a falhas.

## Funcionalidades

- **Round Robin:** distribui as requisições em rodízio entre os servidores saudáveis.
- **Least Connections:** envia cada requisição ao servidor com menos conexões ativas.
- **Health Check em segundo plano:** uma thread verifica os servidores a cada 3 segundos (timeout de 1 s) e guarda o resultado, sem atrasar as requisições.
- **Tolerância a falhas:** se um servidor falha durante uma requisição, ele é marcado como fora do ar e a requisição é reenviada a outro servidor. Se todos caírem, o balanceador responde `503`.
- **Troca de algoritmo em tempo real** e **estatísticas** por rotas HTTP.

## Arquitetura
cd "$HOME\OneDrive\Área de Trabalho\ShopNow"

@'
# ShopNow - Balanceador de Carga

Projeto acadêmico da disciplina de **Sistemas Distribuídos**.

**Autor:** João Nacélio Peixoto Santos

Sistema de balanceamento de carga desenvolvido com **Python**, **Flask** e **Docker**, com três servidores, dois algoritmos de distribuição, monitoramento por Health Check e tolerância a falhas.

## Funcionalidades

- **Round Robin:** distribui as requisições em rodízio entre os servidores saudáveis.
- **Least Connections:** envia cada requisição ao servidor com menos conexões ativas.
- **Health Check em segundo plano:** uma thread verifica os servidores a cada 3 segundos (timeout de 1 s) e guarda o resultado, sem atrasar as requisições.
- **Tolerância a falhas:** se um servidor falha durante uma requisição, ele é marcado como fora do ar e a requisição é reenviada a outro servidor. Se todos caírem, o balanceador responde `503`.
- **Troca de algoritmo em tempo real** e **estatísticas** por rotas HTTP.

## ArquiteturaCliente --> Balanceador (:8080) --+--> Servidor 1 (:5001)
+--> Servidor 2 (:5002)
+--> Servidor 3 (:5003)


## Estrutura do projeto

ShopNow/
├── load_balancer/
│ ├── app.py # Balanceador de carga
│ ├── docker-compose.yml # Orquestração dos 4 containers
│ ├── Dockerfile # Imagem dos servidores
│ └── Dockerfile.lb # Imagem do balanceador
├── server/
│ └── app.py # Servidor de aplicação (/, /health, /slow)
├── tests/
│ └── load_test.py # Teste de carga
└── requirements.txt


## Pré-requisitos

- Docker Desktop
- Python 3 (apenas para rodar o teste de carga)

## Como executar

```bash
git clone https://github.com/joaonacelio/ShopNow-Load-Balancer.git
cd ShopNow-Load-Balancer/load_balancer
docker compose up --build -d
docker compose ps
```

O balanceador fica disponível em `http://localhost:8080`. Os servidores também podem ser acessados diretamente nas portas 5001, 5002 e 5003.

Para encerrar:

```bash
docker compose down
```

## Rotas do balanceador

| Rota | Método | Descrição |
|---|---|---|
| `/` e demais caminhos | GET, POST, PUT, DELETE, PATCH | Encaminha a requisição a um servidor |
| `/algorithm` | GET | Mostra o algoritmo atual |
| `/algorithm` | POST | Troca o algoritmo (`round_robin` ou `least_connections`) |
| `/stats` | GET | Algoritmo, conexões ativas e saúde de cada servidor |
| `/health` | GET | Estado do balanceador |

Rotas dos servidores: `/` (identificação), `/health` e `/slow?seconds=N` (resposta lenta, máximo 30 s, usada nos testes).

## Exemplos de uso (PowerShell)

```powershell
# Trocar o algoritmo
Invoke-RestMethod -Method Post -Uri http://localhost:8080/algorithm -ContentType "application/json" -Body '{"algorithm":"least_connections"}'

# Ver estatísticas
curl.exe http://localhost:8080/stats

# Enviar requisições
1..9 | ForEach-Object { (Invoke-RestMethod http://localhost:8080/).servidor }
```

Em Linux/macOS: `curl -X POST http://localhost:8080/algorithm -H "Content-Type: application/json" -d '{"algorithm":"least_connections"}'`

## Testes realizados

### Round Robin
9 requisições seguidas alternaram entre os servidores: 1, 2, 3, 1, 2, 3, 1, 2, 3.

### Least Connections
Com os Servidores 1 e 2 ocupados por requisições lentas (`/slow?seconds=9`), as 6 requisições rápidas seguintes foram todas atendidas pelo Servidor 3, o único livre. Ao final, as conexões ativas voltaram a 0.

### Health Check e tolerância a falhas
- Servidor 2 parado: `/stats` o marcou como `healthy: false` e as requisições passaram a usar apenas os Servidores 1 e 3, sem erros.
- Servidor religado: voltou ao rodízio automaticamente.
- Os três servidores parados: o balanceador respondeu `503` com a mensagem "Nenhum servidor disponível!" e se recuperou após o religamento.
- **Melhoria medida:** a primeira versão verificava a saúde dos servidores a cada requisição, e uma requisição levava cerca de 3.867 ms com um servidor fora. Com o Health Check em segundo plano, o tempo caiu para cerca de 8 ms.

### Teste de carga

Executado com `tests/load_test.py`:

```bash
python tests/load_test.py --algorithm round_robin --requests 300 --concurrency 20
python tests/load_test.py --algorithm least_connections --requests 60 --concurrency 20 --path "/slow?seconds=0.5"
```

| Cenário | Distribuição (S1 / S2 / S3) | Erros | Throughput | Latência média |
|---|---|---|---|---|
| Round Robin, 300 req | 100 / 100 / 100 | 0 | 423,8 req/s | 45,8 ms |
| Least Connections, 60 req, rota lenta | 21 / 21 / 18 | 0 | 38,0 req/s | 518,0 ms |
| Round Robin, 600 req, Servidor 2 derrubado durante a carga | 258 / 86 / 256 | 0 | 45,8 req/s | 108,5 ms |

No último cenário, o Servidor 2 foi parado durante a carga e religado depois. Ele recebeu apenas 14,3% das requisições, e nenhuma das 600 falhou.

## Limitações conhecidas

- Uma requisição que já está em andamento em um servidor que cai no meio do processamento pode falhar, pois não é reenviada.
- O estado (conexões ativas e algoritmo) fica em memória e é perdido se o balanceador reiniciar.
- O balanceador usa o servidor de desenvolvimento do Flask. Para produção, o recomendado seria um servidor como o Gunicorn.
- Há um único balanceador, que é um ponto único de falha.

## Tecnologias

Python 3.12, Flask 3.1.2, Requests 2.32.5, Docker e Docker Compose.
