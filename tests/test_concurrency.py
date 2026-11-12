from concurrent.futures import ThreadPoolExecutor
import requests

BASE_URL = "http://127.0.0.1:5001"
BOOK_ID = 4


def get_quantity():
    response = requests.get(
        f"{BASE_URL}/info/{BOOK_ID}", timeout=5
    )
    assert response.status_code == 200
    return response.json()["quantity"]


def change_stock(delta):
    if delta == 0:
        return

    response = requests.patch(
        f"{BASE_URL}/update/{BOOK_ID}",
        json={"stock_delta": delta},
        timeout=5
    )
    assert response.status_code == 200


def test_concurrent_purchases():
    original_quantity = get_quantity()

    # Set stock to exactly 3 books
    change_stock(3 - original_quantity)

    try:
        def buy_book(_):
            response = requests.patch(
                f"{BASE_URL}/update/{BOOK_ID}",
                json={"stock_delta": -1},
                timeout=5
            )
            return response.status_code

        # Simulate 8 simultaneous purchase attempts
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(buy_book, range(8)))

        assert results.count(200) == 3
        assert results.count(409) == 5
        assert get_quantity() == 0

    finally:
        # Restore the original inventory
        change_stock(original_quantity - get_quantity())
