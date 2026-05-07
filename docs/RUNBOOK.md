# Operator Runbook

Day-to-day commands for running this stack on a single VPS.

## Spin-up (first time)

```bash
git clone <repo-url> && cd "WhatsApp AI Automation System for Mobile Shop"
cp .env.example .env       # fill in WhatsApp + LLM credentials
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed
```

Open:
- Admin:   http://localhost:3000 (login with `ADMIN_BOOTSTRAP_EMAIL`/`PASSWORD`)
- API:     http://localhost:4000/docs
- n8n:     http://localhost:5678
- Qdrant:  http://localhost:6333/dashboard

## Daily operations

| Task                    | Command                                                          |
|-------------------------|------------------------------------------------------------------|
| Tail backend logs       | `docker compose logs -f backend`                                 |
| Tail n8n logs           | `docker compose logs -f n8n`                                     |
| Restart one service     | `docker compose restart backend`                                 |
| Run a new migration     | `docker compose exec backend alembic revision --autogenerate -m "msg" && alembic upgrade head` |
| Backup the database     | `docker compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql` |
| Restore the database    | `cat backup.sql \| docker compose exec -T postgres psql -U $POSTGRES_USER $POSTGRES_DB` |
| Reset Redis (dev only)  | `docker compose exec redis redis-cli FLUSHALL`                   |

## Adding a product

1. Open admin → Inventory → "Add product"
2. Fill SKU, title, category, brand, price, stock
3. Upload images (drag-drop)
4. Save — instantly searchable by the AI agent

## Running a discount campaign

1. Discounts → New
2. Pick code (e.g. `BACK20`), type (percent/flat), value, expiry
3. Choose what it applies to (categories / brands / specific products)
4. Save → AI will honour the code via the `apply_discount` tool

## When the bot misbehaves

| Symptom                         | First thing to check                                      |
|---------------------------------|-----------------------------------------------------------|
| Bot quotes wrong price          | Tool returned wrong row; check `products` table           |
| Bot keeps chatting after "bye"  | Intent classifier returned non-`goodbye` — check Haiku log|
| Customer not getting replies    | Check `WHATSAPP_ACCESS_TOKEN` validity; check rate limit  |
| Slow replies                    | Check Anthropic API latency; reduce `max_tokens`          |

## Rotating WhatsApp credentials

1. Generate a new system-user access token in Meta Business Manager
2. Update `WHATSAPP_ACCESS_TOKEN` in `.env`
3. `docker compose restart backend`
4. Send a test message — confirm reply arrives
