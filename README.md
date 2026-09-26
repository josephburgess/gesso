# gesso

Portfolio, shop and studio admin for an artist. Django with the Unfold admin, and React pages rendered through [Inertia](https://inertiajs.com).

## Running it

Needs [uv](https://docs.astral.sh/uv/), Node and Docker.

```sh
cp .env.example .env
make up
uv sync && npm install
make migrate
uv run manage.py createsuperuser
make dev
```

The site runs at http://localhost:8000, with the admin at `/admin`. Emails print to the terminal.

## Commands

| Command                             | Does                                                    |
| ----------------------------------- | ------------------------------------------------------- |
| `make dev`                          | Runs Django and Vite together                           |
| `make up` / `make down`             | Starts or stops Postgres in Docker                      |
| `make test`                         | Runs the tests                                          |
| `make check`                        | Type checks with `ty` and checks for missing migrations |
| `make fmt`                          | Formats Python (ruff) and TypeScript (prettier)         |
| `make lint`                         | Checks formatting and lint without changing anything    |
| `make migrate`                      | Applies migrations                                      |
| `make schema app=<app> name=<name>` | Makes a schema migration named `schema_<name>`          |
| `make data app=<app> name=<name>`   | Makes an empty data migration named `data_<name>`       |
| `make prod-manage cmd=<command>` | Runs a `manage.py` command on the production server |

Before committing run `make fmt lint check test`.
