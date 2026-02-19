\# ERI Backend



Engineering Reasoning Index — assessment engine backend.



\## Stack

\- FastAPI

\- PostgreSQL

\- Firebase Auth

\- Docker

\- Alembic



\## Local Run



docker compose up --build



\## Environment



Create .env with:



DATABASE\_URL=

FIREBASE\_SERVICE\_ACCOUNT=



\## Architecture



Institution-grade digital examination engine:

\- attempt lifecycle

\- question caching

\- deterministic option shuffling

\- bonus gating

\- ranking engine



