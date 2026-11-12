# Partner Handoff — End of Chunk 1

## Completed Work

The Catalog service and the Search/Info portion of the
Front-end are implemented.

Both services communicate using HTTP REST and JSON.

Docker Compose currently manages two Linux containers.

## Catalog Service

Internal Docker address: http://catalog:5000
Host address: http://localhost:5001

Endpoints:

GET /health
GET /search/<topic>
GET /info/<id>
PATCH /update/<id>

Update request examples:

{"stock_delta": -1}
{"stock_delta": 5}
{"price": 60}

Only one update field is accepted per request.

Stock updates are atomic and cannot produce negative inventory.

Important responses:
- 200: Successful operation
- 400: Invalid update request
- 404: Book not found
- 409: Insufficient stock

## Front-end Service

Host address: http://localhost:5000

Implemented:
GET /search/<topic>
GET /info/<id>

The Front-end forwards requests to Catalog using HTTP.

## Database

Catalog uses SQLite.

The initial four books are inserted automatically when
the database is first initialized.

Docker stores the database in a persistent named volume.

Existing inventory is not reset during application restarts.

## Work Remaining for Partner

1. Implement the Order microservice.
2. Create a separate persistent SQLite orders database.
3. Implement POST /purchase/<id>.
4. Query Catalog to check item availability.
5. Decrease inventory through Catalog's Update API.
6. Record purchase results and handle failures.
7. Add Purchase forwarding to Front-end.
8. Add Order to Docker Compose as the third container.
9. Implement the host command-line client.
10. Complete end-to-end and failure testing.
11. Record actual program output in docs/.
12. Prepare the required 2–3 page design document.

## Important Design Notes

Order must communicate with Catalog through HTTP,
not by directly accessing Catalog's SQLite database.

Catalog stock decrements are atomic, preventing overselling.

The complete purchase operation is not yet an atomic
transaction across Catalog and Order databases.

Use the existing environment-variable configuration for
service URLs and database paths.

Do not overwrite the existing Catalog implementation.
Extend the project using feature branches and Pull Requests.
