# WhatsApp AI Automation System for Mobile Shop

End-to-end WhatsApp-driven sales assistant for a mobile phone shop.
Customers chat on WhatsApp, an AI agent understands intent, searches the
shop's inventory, replies with grounded data (no hallucinations), remembers
past conversations, hands off to humans when needed, and ends chats cleanly.
Shop staff manage everything through a polished Next.js admin dashboard.
n8n orchestrates the message flow.

> **Status:**  full-stack architecture demonstrating
> WhatsApp Cloud API + n8n + RAG + tool-using LLM agents + Next.js admin UI.

---

## Architecture

```
Customer WhatsApp
       │
       ▼
WhatsApp Cloud API (Meta webhook)
       │
       ▼
n8n Orchestrator  ──►  FastAPI Backend
                              │
                ┌─────────────┼──────────────┬─────────────┐
                ▼             ▼              ▼             ▼
           PostgreSQL      Redis         Qdrant       LLM Provider
        (products,      (sessions,    (chat memory,   (Claude /
         customers,      tokens,       product RAG)    OpenAI)
         orders,         rate-limit)
         discounts)

                  Admin Dashboard (Next.js 14 + Tailwind + shadcn/ui)
                  - Inventory CRUD
                  - Categories & brands
                  - Live inbox (human takeover)
                  - Discounts / broadcasts
                  - Analytics
```

## Tech Stack

| Layer            | Choice                                    |
|------------------|-------------------------------------------|
| Messaging        | WhatsApp Cloud API (official Meta)        |
| Orchestration    | n8n (Docker, self-hosted)                 |
| Backend API      | FastAPI + SQLAlchemy 2 + Pydantic v2      |
| Database         | PostgreSQL 16                             |
| Cache / Sessions | Redis 7                                   |
| Vector DB        | Qdrant                                    |
| LLM              | Claude Sonnet (tool use) / OpenAI gpt-4o  |
| Admin UI         | Next.js 14 + Tailwind + shadcn/ui         |
| Auth (admin)     | NextAuth + JWT                            |
| Hosting          | Docker Compose on a Linux VPS             |
| Monitoring       | Grafana + Loki + Prometheus               |

## Repository Layout

```
.
├── backend/             FastAPI app + SQLAlchemy models + Alembic + LLM tools
├── admin-dashboard/     Next.js 14 admin panel
├── database/            SQL migrations + seed data
├── n8n/                 Workflow JSON exports
├── docker/              Per-service Dockerfiles + configs
├── docs/                Implementation plan, runbook, API spec
├── scripts/             Helper scripts (seed, backup, restore)
├── docker-compose.yml   One-command stack spin-up
└── .env.example         Environment template
```

## Quick Start

```bash
# 1. Clone
git clone <repo-url> && cd "WhatsApp AI Automation System for Mobile Shop"

# 2. Configure
cp .env.example .env
# edit .env with your WhatsApp / LLM credentials

# 3. Spin up the stack
docker compose up -d

# 4. Run migrations + seed
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed

# 5. Open
# Admin dashboard:  http://localhost:3000
# Backend API:      http://localhost:4000  (Swagger at /docs)
# n8n:              http://localhost:5678
# Qdrant:           http://localhost:6333
```

## Implementation Phases

| Phase | Weeks | Deliverable                                                                   |
|-------|-------|-------------------------------------------------------------------------------|
| 1     | 1–2   | VPS + Docker stack + WhatsApp webhook echoes "hello"                          |
| 2     | 3–4   | Postgres schema + admin CRUD for products / categories / brands               |
| 3     | 5–6   | Tool-using LLM agent + intent classifier + n8n WF-1 / WF-2                    |
| 4     | 7     | Qdrant memory + nightly summary + category-context routing                    |
| 5     | 8     | Human handoff (WF-3) + clean end-conversation (WF-4) + live inbox             |
| 6     | 9–10  | Discount engine + broadcast composer + rate-limited sender                    |
| 7     | 11–12 | Analytics, Grafana boards, load test, hardening, docs, walkthrough            |

Full plan in [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md).

## Anti-Hallucination Guardrails

The LLM **only** sees tool outputs — it never makes up prices, stock, or specs.

1. **Tool-only data access.** `search_products`, `get_product`,
   `apply_discount`, `start_human_handoff`, `end_conversation`. The system
   prompt forbids quoting any number not returned by a tool.
2. **Pre-filter intent classifier.** A cheap model labels each message
   (greeting / product_inquiry / price_check / complaint / human_request /
   goodbye / spam) and routes complaints + low-confidence straight to a human.
3. **Clean exit.** `goodbye` intent triggers `end_conversation` with a closing
   template — no rambling, no false chatting.

## Memory Layers

| Layer       | What                              | Where     | Window        |
|-------------|-----------------------------------|-----------|---------------|
| Short-term  | Last 10 messages of current convo | Redis     | session       |
| Mid-term    | Daily summary per customer        | Postgres  | rolling 7 d   |
| Long-term   | Embeddings of every past message  | Qdrant    | forever       |

Every customer turn pulls last-10 + summary + top-5 RAG hits into the prompt.

## Security

- WhatsApp webhook HMAC-SHA256 signature verification
- Server-side chat tokens (never sent over WhatsApp), 24 h TTL, hashed at rest
- Per-phone Redis rate limit (30 msg / 5 min) to block spam
- JWT + RBAC for admin (owner / staff / viewer)
- Customer phone numbers encrypted at rest; access logged in `audit_log`
- STOP / UNSUBSCRIBE handler (WhatsApp policy)

## License

MIT — see [`LICENSE`](LICENSE).

---

Built as a portfolio project demonstrating production-grade AI automation
architecture: WhatsApp Cloud API, n8n orchestration, RAG over conversation
history, tool-using LLM agents, and a modern admin dashboard.
