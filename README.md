# Bazar.com — Distributed Operating Systems Lab 1

A multi-tier online bookstore built using Python, Flask, SQLite,
HTTP REST APIs, and Docker Compose.

## Architecture

The application consists of three microservices:

1. Front-end: Receives client requests and forwards them.
2. Catalog: Manages books, prices, and inventory.
3. Order: Handles purchases and order history (not yet implemented).

Current request flow:

Client -> Front-end -> Catalog -> Front-end -> Client

## Requirements

- Docker Desktop with Linux containers
- Docker Compose
- Python (for running the automated tests)

## Running the Application

From the project root:

    docker compose up --build -d

Check running services:

    docker compose ps

## API Examples

Search for books:

    curl "http://localhost:5000/search/distributed%20systems"

Get book information:

    curl http://localhost:5000/info/2

Update inventory directly through Catalog:

    curl -X PATCH http://localhost:5001/update/2 \
      -H "Content-Type: application/json" \
      -d '{"stock_delta":5}'

Update a price:

    curl -X PATCH http://localhost:5001/update/2 \
      -H "Content-Type: application/json" \
      -d '{"price":60}'

## Running Tests

Create and activate a Python virtual environment, then install:

    python -m pip install -r requirements-dev.txt

Run:

    python -m pytest tests/ -v

The integration tests require the Docker services to be running.
Some tests temporarily modify inventory.

## Logs

    docker compose logs -f

## Stopping

    docker compose down

Database information persists in a Docker named volume.
Do not use `docker compose down -v` unless you intend to
delete the stored data.

## Current Status

Implemented:
- Catalog database and initial book records
- Catalog Search, Info, and Update APIs
- Atomic stock updates
- Front-end Search and Info forwarding
- Docker Compose with two running services
- Persistent Catalog SQLite storage
- Automated Catalog and concurrency tests

Remaining:
- Order service and persistent order history
- Front-end Purchase endpoint
- Third Docker container
- Host command-line client
- Final integration tests and submission documentation
