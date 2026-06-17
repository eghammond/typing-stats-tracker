# Typing Stats Tracker - API

A REST API for recording results of typing speed tests, and computing per-user statistics. Built with FastAPI and PostgreSQL. This repository contains the backend only; the frontend lives in a repository that is currently being developed. I will add the link here when I am done with it.

## Tech stack

- **FastAPI** — web framework
- **PostgreSQL** — database
- **SQLAlchemy** — ORM
- **python-jose** — JWT encoding/decoding
- **argon2-cffi** — password hashing
- **slowapi** — rate limiting
- **pytest** — testing
- **Railway** — deployment

## Running locally

These steps get the API running locally.

### Prerequisites

- Python 3.11+
- PostgreSQL running locally

### Setup

```bash
# 1. Clone the repo
git clone git@github.com:yourusername/typing-stats-tracker.git
cd typing-stats-tracker

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file in the project root (see "Environment variables" below)

# 5. Make sure PostgreSQL is running, then start the app
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`, with interactive documentation at `http://127.0.0.1:8000/docs`.

## Environment variables

Create a `.env` file in the project root with the following:

| Variable       | Description                                  |
| -------------- | -------------------------------------------- |
| `SECRET_KEY`   | Secret used to sign JWTs. Use a long, random value. |
| `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://user@localhost/typingstats`. |

You can generate a secure secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

The `.env` file is git-ignored and should never be committed.

## API overview

All request and response bodies are JSON. Protected endpoints require an `Authorization: Bearer <token>` header.

| Method | Endpoint          | Auth | Description                                  |
| ------ | ----------------- | ---- | -------------------------------------------- |
| POST   | `/auth/register`  | No   | Create a new user account.                   |
| POST   | `/auth/login`     | No   | Log in and receive a JWT access token.       |
| POST   | `/results`        | Yes  | Submit a typing-test result.                 |
| GET    | `/results`        | Yes  | List the current user's results.             |
| GET    | `/results/stats`  | Yes  | Aggregate stats (avg/best WPM, accuracy).    |

Access tokens expire 30 minutes after login; clients must log in again to obtain a new one. Authentication endpoints are rate limited to mitigate brute-force attempts.

## Running the tests

The test suite uses an isolated SQLite database, so it does not touch your development data.

```bash
python -m pytest app/tests/ -v
```

## Project structure

```
typing-stats-tracker/
├── app/
│   ├── main.py          # FastAPI app and route definitions
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── database.py      # Engine, session, and DB dependency
│   └── tests/
│       └── test_main.py # API tests
├── requirements.txt
├── Procfile             # Start command for deployment
└── README.md
```

## Deployment

The API is deployed on Railway. Railway provisions PostgreSQL and injects `DATABASE_URL`; `SECRET_KEY` is set manually in the service variables. The start command is defined in the `Procfile`.

## Acknowledgements

Built as a learning project. I used an AI assistant (Claude) as a tutor while building this — for explaining concepts, reviewing my code, and debugging — while writing the code myself. Claude also helped me write this README.