"""Non-destructive-to-production validation; run ONLY against isolated Compose project.

Run: bash tests/run_validation.sh
"""
import json
import os
import sqlite3
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import requests

FRONTEND = os.getenv("BAZAR_TEST_FRONTEND", "http://127.0.0.1:5100").rstrip("/")
CATALOG = os.getenv("BAZAR_TEST_CATALOG", "http://127.0.0.1:5101").rstrip("/")
PROJECT = os.getenv("BAZAR_TEST_PROJECT", "shaker_bazar_validation")


def request(method, url, *, json_body=None):
    response = requests.request(method, url, json=json_body, timeout=12)
    return response.status_code, response.json()


def checked(method, url, expected, *, json_body=None):
    status, data = request(method, url, json_body=json_body)
    print(f"{method} {url} -> HTTP {status}: {json.dumps(data, ensure_ascii=False)}")
    assert status == expected, (status, expected, data)
    return data


def count_orders():
    command = [
        "docker", "compose", "-p", PROJECT, "exec", "-T", "order", "python", "-c",
        "import sqlite3; c=sqlite3.connect('file:/data/orders.db?mode=ro',uri=True); "
        "print(c.execute('SELECT COUNT(*) FROM orders').fetchone()[0]); c.close()",
    ]
    return int(subprocess.check_output(command, text=True).strip())


def wait_healthy(url, seconds=45):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if requests.get(url + "/health", timeout=2).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise AssertionError(f"Service did not become ready: {url}")


def purchase(barrier, serial):
    barrier.wait(timeout=10)
    status, data = request("POST", FRONTEND + "/purchase/4")
    return serial, status, data


def main():
    print("BAZAR.COM ISOLATED EXECUTION EVIDENCE")
    print("Target: " + FRONTEND)
    print("Docker Compose test project: " + PROJECT)
    print("Tests use disposable test volumes; NOT the real bookstore database.\n")

    wait_healthy(FRONTEND)
    wait_healthy(CATALOG)

    print("SECTION A: HOST CLIENT / REST APIS")
    matches = checked("GET", FRONTEND + "/search/distributed%20systems", 200)
    assert [x["id"] for x in matches] == [1, 2]
    matches = checked("GET", FRONTEND + "/search/undergraduate%20school", 200)
    assert [x["id"] for x in matches] == [3, 4]
    assert checked("GET", FRONTEND + "/search/nonexistent", 200) == []
    checked("GET", FRONTEND + "/info/2", 200)
    checked("GET", FRONTEND + "/info/999", 404)
    checked("POST", FRONTEND + "/purchase/999", 404)
    print("READ-ONLY AND INVALID-ID API TESTS PASSED\n")

    print("SECTION B: CATALOG PRICE AND INVENTORY UPDATE")
    book3 = checked("GET", CATALOG + "/info/3", 200)
    original_price = book3["price"]
    new_price = original_price + 1
    checked("PATCH", CATALOG + "/update/3", 200, json_body={"price": new_price})
    assert checked("GET", CATALOG + "/info/3", 200)["price"] == new_price
    checked("PATCH", CATALOG + "/update/3", 200, json_body={"price": original_price})
    original_stock = book3["quantity"]
    checked("PATCH", CATALOG + "/update/3", 200, json_body={"stock_delta": 2})
    assert checked("GET", CATALOG + "/info/3", 200)["quantity"] == original_stock + 2
    checked("PATCH", CATALOG + "/update/3", 200, json_body={"stock_delta": -2})
    checked("PATCH", CATALOG + "/update/3", 409, json_body={"stock_delta": -1000})
    assert checked("GET", CATALOG + "/info/3", 200)["quantity"] == original_stock
    print("CATALOG UPDATE TESTS PASSED\n")

    print("SECTION C: FULL CONCURRENT PURCHASE")
    start_stock = checked("GET", CATALOG + "/info/4", 200)["quantity"]
    assert start_stock >= 1
    if start_stock != 1:
        checked("PATCH", CATALOG + "/update/4", 200,
                json_body={"stock_delta": 1 - start_stock})
    assert checked("GET", FRONTEND + "/info/4", 200)["quantity"] == 1
    assert count_orders() == 0, "Expected fresh isolated order database"

    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(purchase, barrier, number) for number in (1, 2)]
        results = [future.result(timeout=20) for future in futures]

    for serial, status, payload in results:
        print(f"Purchase request {serial}: HTTP {status}: {payload}")
    assert sorted(status for _, status, _ in results) == [200, 409]
    assert checked("GET", FRONTEND + "/info/4", 200)["quantity"] == 0
    checked("POST", FRONTEND + "/purchase/4", 409)
    assert count_orders() == 1
    print("FULL PURCHASE CONCURRENCY TEST PASSED: 1 success, 1 conflict, 0 stock, 1 order\n")

    print("SECTION D: PERSISTENCE AFTER RESTART")
    subprocess.run(["docker", "compose", "-p", PROJECT, "restart"], check=True)
    wait_healthy(FRONTEND)
    assert checked("GET", FRONTEND + "/info/4", 200)["quantity"] == 0
    assert count_orders() == 1
    print("PERSISTENCE TEST PASSED: stock=0, completed orders=1")
    print("\nALL ISOLATED VALIDATION CHECKS PASSED")


if __name__ == "__main__":
    main()
