import requests


def test_search_distributed_systems():
    response = requests.get(
        "http://127.0.0.1:5001/search/distributed%20systems",
        timeout=5
    )

    assert response.status_code == 200

    books = response.json()

    assert len(books) == 2
    assert books[0]["id"] == 1
    assert books[1]["id"] == 2


def test_info_existing_book():
    response = requests.get(
        "http://127.0.0.1:5001/info/2",
        timeout=5
    )

    assert response.status_code == 200

    book = response.json()

    assert book["title"] == "RPCs for Noobs"
    assert isinstance(book["quantity"], int)
    assert book["quantity"] >= 0
    assert isinstance(book["price"], int)


def test_info_nonexistent_book():
    response = requests.get(
        "http://127.0.0.1:5001/info/99",
        timeout=5
    )

    assert response.status_code == 404
    assert response.json()["error"] == "Book not found"


def test_invalid_stock_update():
    response = requests.patch(
        "http://127.0.0.1:5001/update/2",
        json={"stock_delta": "five"},
        timeout=5
    )

    assert response.status_code == 400


def test_stock_update():
    url = "http://127.0.0.1:5001"

    # Get the original quantity
    response = requests.get(f"{url}/info/2", timeout=5)
    assert response.status_code == 200
    original_quantity = response.json()["quantity"]

    # Add one book
    response = requests.patch(
        f"{url}/update/2",
        json={"stock_delta": 1},
        timeout=5
    )
    assert response.status_code == 200

    try:
        # Verify the quantity increased
        response = requests.get(f"{url}/info/2", timeout=5)
        assert response.status_code == 200
        assert response.json()["quantity"] == original_quantity + 1

    finally:
        # Restore the original quantity
        response = requests.patch(
            f"{url}/update/2",
            json={"stock_delta": -1},
            timeout=5
        )
        assert response.status_code == 200
