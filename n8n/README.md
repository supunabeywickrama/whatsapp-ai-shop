# n8n Workflows

Each JSON in `workflows/` is an exported n8n workflow. To import:

1. Open n8n at http://localhost:5678 (login with `N8N_BASIC_AUTH_USER`/`PASSWORD`).
2. Workflows → Import from File → pick the JSON.
3. Set credentials (WhatsApp access token, backend base URL, etc.).
4. Activate.

## Workflows

| File                         | Purpose                                                  |
|------------------------------|----------------------------------------------------------|
| `wf-1-inbound.json`          | WhatsApp webhook → verify → upsert customer → classify   |
| `wf-2-ai-reply.json`         | Build context → call backend `/api/ai/turn` → send reply |
| `wf-3-handoff.json`          | Mark conversation awaiting_human → notify staff          |
| `wf-4-end-conversation.json` | Send closing template → close conversation               |
| `wf-5-broadcast.json`        | Audience query → rate-limited template send loop         |
| `wf-6-daily-summary.json`    | Cron 00:30 → generate per-customer summary + embeddings  |

The placeholder JSONs below are minimal — they import cleanly into n8n but
you'll wire credentials and the exact node graph in Phase 3.
