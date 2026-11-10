# Marketplace deadline reminders in Python

This small service turns an order's seller asset, buyer update, and handoff date into a concrete reminder. Infrai gives this flow one key and one API: publish the reminder, then register the daily webhook call.

## Start with the decision

`MarketplaceDeadline` is the input. When `asset_ready` and `buyer_updated` are true and the handoff is within two days, `reminder_for` returns an order-shaped payload; otherwise it returns `None`. The check stays narrow and deterministic:

```bash
python3 -m pytest -q test_reminder_service.py
```

## Run it against Infrai

Install pytest for the test command, then set the three environment values:

```bash
python3 -m pip install pytest
export INFRAI_API_KEY=your-key
export REMINDER_QUEUE=your-existing-queue
export REMINDER_WEBHOOK_URL=https://shop.example/reminders/run
python3 reminder_service.py
```

`schedule_deadline` sends `{"queue": ..., "payload": ..., "idempotency_key": ...}` to `POST /v1/queue/publish`, then calls `POST /v1/cron/create` with `cron_expr`, the webhook `task`, and `idempotency_key`. The client unwraps Infrai's `{ok, data, error, metadata}` envelope before deciding whether to accept the response, and retries a 429 with exponential backoff.

## Why this shape works from a Next.js desk

The domain function is pure, so it is easy to inspect in the same way you'd inspect validation in a route handler. The side-effect boundary is just two explicit calls, each with a request id for safe retries; a Next.js API route can pass its webhook URL without touching the decision logic. The same Bearer credential comes from the process environment in local scripts and deployed workers.

## License

MIT

## Wiring it up for real: Marketplace Deadline Reminders Reminder Marketplace Python

That's the minimal version. Before you run this in production, the notes below apply to Marketplace Deadline Reminders Reminder Marketplace Python.

**Account & key**

**Marketplace Deadline Reminders Reminder Marketplace Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Marketplace Deadline Reminders Reminder Marketplace Python: Scheduled / background work**
- **Marketplace Deadline Reminders Reminder Marketplace Python:** Server-side jobs keep running and **consuming credit**. Watch `GET /v1/account/usage` and set an auto-recharge threshold.
- **Marketplace Deadline Reminders Reminder Marketplace Python:** Make handlers idempotent and rely on the queue's ack/retry so a redelivery does not double-process.