# Implementation Plan

End-to-end WhatsApp-driven sales assistant for a mobile phone shop. Customers
chat on WhatsApp; the system understands intent, searches inventory, replies
as a grounded AI sales agent, remembers past chats, hands off to humans, and
ends conversations cleanly. Staff manage everything through a Next.js admin
dashboard. n8n orchestrates the message flow.

---

## 1. Architecture

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
```

## 2. Tech Stack

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

## 3. Database Schema (key tables)

- `categories` — id, name, parent_id (for sub-categories), icon_url, sort_order
- `brands` — id, name, logo_url
- `products` — id, sku, category_id, brand_id, title, description, condition
  (new/used/refurbished), price, discounted_price, stock_qty, images, specs,
  is_active
- `customers` — id, phone (unique e164), name, locale, opt_in_marketing, tags,
  summary (mid-term memory), last_seen_at
- `conversations` — id, customer_id, status (active/awaiting_human/closed),
  category_context, chat_token_hash, token_expires_at, started_at, closed_at,
  close_reason
- `messages` — id, conversation_id, direction (in/out), sender (customer/ai/
  agent/system), body, intent_label, confidence, created_at
- `discounts` — id, code, type (percent/flat), value, applies_to, starts_at,
  ends_at, max_uses, used_count, is_active
- `broadcasts` — id, title, audience_filter, template_name, scheduled_at,
  sent_count, status
- `audit_logs` — id, actor_id, action, entity, entity_id, payload, created_at

## 4. Memory Layers

| Layer       | What                              | Where     | Window        |
|-------------|-----------------------------------|-----------|---------------|
| Short-term  | Last 10 messages of current convo | Redis     | session       |
| Mid-term    | Daily summary per customer        | Postgres  | rolling 7 d   |
| Long-term   | Embeddings of every past message  | Qdrant    | forever       |

Every customer turn pulls last-10 + summary + top-5 RAG hits into the prompt.
A nightly cron condenses yesterday's messages into the summary and pushes
embeddings to Qdrant.

## 5. Anti-Hallucination Guardrails

1. **Tool-only data access.** The LLM is given five tools: `search_products`,
   `get_product`, `apply_discount`, `start_human_handoff`, `end_conversation`.
   The system prompt forbids quoting any number not returned by a tool.
2. **Pre-filter intent classifier.** Claude Haiku labels each message
   (greeting / product_inquiry / price_check / complaint / human_request /
   goodbye / spam) and routes complaints + low-confidence straight to a human.
3. **Clean exit.** A `goodbye` intent triggers `end_conversation` with a
   closing template — no rambling, no false chatting.

## 6. n8n Workflows

| File                         | Purpose                                                  |
|------------------------------|----------------------------------------------------------|
| `wf-1-inbound.json`          | WhatsApp webhook → verify → upsert customer → classify   |
| `wf-2-ai-reply.json`         | Build context → call backend `/api/ai/turn` → send reply |
| `wf-3-handoff.json`          | Mark conversation awaiting_human → notify staff          |
| `wf-4-end-conversation.json` | Send closing template → close conversation               |
| `wf-5-broadcast.json`        | Audience query → rate-limited template send loop         |
| `wf-6-daily-summary.json`    | Cron 00:30 → generate per-customer summary + embeddings  |

## 7. Phase-by-Phase Build Plan

### Phase 1 — Foundations (Week 1–2)
- VPS + Docker Compose stack (Postgres, Redis, n8n, Qdrant, backend, admin)
- Meta Business account + WhatsApp Cloud API number + webhook verification
- Bootstrap admin user + JWT login
- **Deliverable:** webhook test echoes "hello" back to the customer.

### Phase 2 — Inventory & Admin (Week 3–4)
- Alembic migrations from SQLAlchemy models
- CRUD APIs for categories, brands, products
- Admin pages: inventory table, category tree, brand list, CSV import
- Image upload (S3-compatible)
- **Deliverable:** shop can manage their full catalog from the dashboard.

### Phase 3 — Core AI Chat (Week 5–6)
- Intent classifier (Haiku) wired
- Tool-using agent (`search_products`, `get_product`, etc.)
- Short-term memory in Redis (last 10 messages)
- n8n WF-1 and WF-2 active
- **Deliverable:** customer can ask "do you have iPhone 13 chargers?" and
  get a grounded reply with price.

### Phase 4 — Memory & Categories Routing (Week 7)
- Qdrant collection bootstrap, embedding pipeline
- Nightly summary cron (WF-6)
- RAG retrieval injected into agent prompts
- `category_context` on conversations sticks across turns
- **Deliverable:** bot remembers returning customers; follow-up questions
  feel natural.

### Phase 5 — Human Handoff & Clean End (Week 8)
- WF-3 (handoff) + WF-4 (end conversation)
- Live inbox in admin dashboard
- Take-over button in the UI
- Goodbye / low-confidence detection that ends the chat with a closing
  template instead of looping
- **Deliverable:** no more bot rambling; staff can step in any time.

### Phase 6 — Discounts & Broadcasts (Week 9–10)
- Discount engine + `apply_discount` tool
- Broadcast composer + template approval flow
- Rate-limited sender (WhatsApp throttles ~80 msg/sec)
- **Deliverable:** shop can run a "20% off all back covers this weekend"
  campaign in 2 minutes.

### Phase 7 — Polish, Analytics, Hardening (Week 11–12)
- Dashboard charts (Recharts)
- Grafana boards (Loki + Prometheus)
- Load test, chaos test (DB down, LLM timeout)
- Pen test of admin auth
- Operator runbook + Loom walkthrough
- **Deliverable:** production-ready system.

### Optional Phase 8 — Orders & Payments (+3 weeks)
- Cart on conversation
- Payment link generator (Stripe / local PSP)
- Order tracking page

## 8. Security Checklist

- WhatsApp webhook HMAC-SHA256 signature verification
- All admin endpoints behind JWT + RBAC (`owner`, `staff`, `viewer`)
- Server-side chat tokens (never sent over WhatsApp), 24h TTL, hashed at rest
- Per-phone Redis rate limit (30 msg / 5 min) to block spam
- Encrypted phone numbers at rest; access logged in `audit_logs`
- Secrets in `.env` + Docker secrets, never in n8n exports
- Nightly `pg_dump` to S3-compatible storage, 30-day retention
- STOP / UNSUBSCRIBE handler — required by WhatsApp policy

## 9. Cost Estimate (steady state)

| Item                                            | Est. cost          |
|-------------------------------------------------|--------------------|
| VPS (4 vCPU / 8GB / 160GB)                      | $30                |
| WhatsApp Cloud API (after free tier, ~5k convos)| $40–80             |
| LLM tokens (Haiku classify + Sonnet replies)    | $60–150            |
| Domain + Let's Encrypt SSL                      | $1                 |
| Backups (S3)                                    | $5                 |
| **Total**                                       | **~$140–270 / mo** |

Tunable: Haiku-only mode drops LLM cost 5–10×.

## 10. Risks & Mitigations

| Risk                          | Mitigation                                                |
|-------------------------------|-----------------------------------------------------------|
| WhatsApp policy violation     | Cloud API only; honor STOP; templates outside 24h window  |
| LLM hallucinates prices       | Tool-only data access + automated regression tests        |
| Customer data leak            | Encryption at rest, JWT+RBAC, audit log, signed webhooks  |
| Bot loops / "false chatting"  | Intent classifier + `end_conversation` + max-turns ceiling|
| n8n bottleneck                | Async workflows; backend has its own queue                |
| Cost spike from spam          | Rate-limit per phone; flag accounts >X msg/hour           |
