# Bazar.com - Distributed Online Book Store
## Distributed and Operating Systems - Lab 1 Design Report

**System:** Bazar.com | **Architecture:** Two tiers, three independent microservices
**Implementation:** Python, Flask, HTTP REST, SQLite, Linux Docker containers, Docker Compose

### 1. Purpose and architecture

Bazar.com demonstrates a small distributed bookstore with four books and two categories: *distributed systems* (books 1 and 2) and *undergraduate school* (books 3 and 4). The assignment requires `search(topic)`, `info(item_number)`, and `purchase(item_number)`. The implementation has **two logical tiers**, not three: a client-facing Frontend tier and a backend tier containing the independently running Catalog and Order microservices.

```text
Host CLI / curl
       |
       v
 Frontend (HTTP :5000)
   |             |
   | GET         | POST
   v             v
 Catalog <---- Order
   |   HTTP       |
 SQLite       SQLite
 volume       volume
```

Frontend forwards search and information requests to Catalog and purchase requests to Order. Order communicates directly with Catalog over the Docker Compose network. Each component runs in a separate Linux container. The host reaches Frontend at `127.0.0.1:5000`; Catalog is additionally exposed on host port `5001` for direct API testing. Docker's internal DNS resolves backend hostnames such as `catalog` without hard-coding changing container IP addresses.

### 2. Service responsibilities and REST API

**Catalog:** The existing SQLite database stores each book's ID, title, topic, price, and quantity. `GET /search/<topic>` returns matching titles and IDs. `GET /info/<id>` returns a book's title, price and quantity (or HTTP 404). `PATCH /update/<id>` changes the price via `{"price": integer}` or inventory via `{"stock_delta": integer}`. Negative prices, invalid deltas, and insufficient stock are rejected.

**Frontend:** `GET /search/<topic>`, `GET /info/<id>`, and `POST /purchase/<id>` forward requests to the correct backend, return JSON, and preserve HTTP status codes. Requests use timeouts; unavailable backends produce errors rather than hanging indefinitely.

**Order:** `POST /purchase/<id>` first calls Catalog's information endpoint over HTTP. If no stock remains, it returns HTTP 409. Otherwise it requests `PATCH /update/<id>` with `stock_delta: -1`. A successful decrement is followed by an insertion into a separate SQLite `orders` table containing order ID, book ID, title, price, status, and timestamp. Success returns a JSON message beginning with `bought book ...`. The order file persists in its own Docker volume.

### 3. Concurrency, persistence, and failure behavior

Multiple clients may issue requests concurrently. A straightforward read-then-write on Catalog stock can oversell the final copy. The existing Catalog code instead issues a *single conditional SQLite update*: `UPDATE books SET quantity = quantity + ? WHERE id = ? AND quantity + ? >= 0`. SQLite serializes competing writers, and a second request cannot decrement zero stock. Order must check the response from this final atomic update even if its earlier availability check was positive. A temporary test environment with only one copy is used to demonstrate that two concurrent purchase attempts should yield one HTTP 200 and one HTTP 409, zero remaining stock, and one completed order.

Docker named volumes `catalog-data` and `order-data` retain SQLite data outside container writable layers. The validation script checks stock and order records before and after restarting all three containers. This is a demonstration of persistence across container restarts; deleting volumes intentionally destroys those databases.

If Catalog is unreachable, the gateway or Order returns a controlled service-unavailable response. **Known limitation:** Catalog's decrement and Order's insert are separate transactions. If the Order database insert fails after a successful decrement, stock may be reduced without a saved order. A timeout after Catalog commits can also leave an uncertain result. The implementation reports these cases but does not provide automatic compensation, exactly-once semantics, or distributed transactions.

### 4. Deployment, verification, and logs

`docker compose up -d --build` builds and starts the three services; `docker compose ps` displays their status. A client on the host operating system can issue `curl http://127.0.0.1:5000/info/2` or run `python client/bazar_cli.py search 'distributed systems'`. The client formats query output and purchase messages; service logs show corresponding requests, stock changes (from Catalog access logs and API output), and successful purchase messages from Order.

The reproducible isolated test command is `bash tests/run_validation.sh`. It runs with distinct test project containers, test databases and alternate host ports, then creates `docs/sample-output.txt` from actual execution and retains the service logs in `docs/service-logs.txt`. No results are claimed until the script has been executed successfully in a Docker-enabled environment. The original Catalog tests remain available for direct API testing but may change persistent stock.

### 5. Tradeoffs and possible extensions

Flask and SQLite minimize setup and complexity. REST and JSON make service boundaries explicit, at the cost of network latency and temporary failures. SQLite supports small workloads and atomic local inventory updates but limits concurrent writers compared with a larger database. Docker Compose makes local deployment repeatable but is not a multi-machine orchestrator. An improved design would use unique purchase identifiers for idempotent retries, an order state machine and reconciliation/compensation for partial failures, stronger failure-injection tests, production WSGI servers, and health-checked startup. Authentication, payments, caching, replication, and high-availability deployment are intentionally outside the scope of this first lab.

### 6. Conclusion

Bazar.com is designed to meet Lab 1's core requirements: four-book Catalog, REST-based Frontend and Order workflows, three separately containerized services, persistent Catalog and order records, stock-update concurrency protection, and reproducible host-client tests. Its intentionally limited cross-service transaction guarantees are explicitly documented so the demonstration distinguishes tested behavior from production reliability.
