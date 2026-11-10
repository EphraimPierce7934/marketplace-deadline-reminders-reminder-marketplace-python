from datetime import date

from reminder_service import MarketplaceDeadline, reminder_for


def test_ready_order_due_tomorrow_gets_handoff_reminder():
    item = MarketplaceDeadline("order-7", True, True, date(2026, 9, 5))
    assert reminder_for(item, date(2026, 9, 4)) == {"order_id": "order-7", "kind": "handoff", "days_left": 1}


def test_unready_asset_does_not_notify():
    item = MarketplaceDeadline("order-8", False, True, date(2026, 9, 5))
    assert reminder_for(item, date(2026, 9, 4)) is None


def test_schedule_transmits_queue_and_idempotency_keys():
    from unittest.mock import patch
    from infrai_client import InfraiClient
    from reminder_service import schedule_deadline

    client = InfraiClient("test-key")
    item = MarketplaceDeadline("order-7", True, True, date(2026, 9, 5))
    with patch.object(client, "_request", return_value={}) as request:
        schedule_deadline(item, "https://example.test/reminders", client, date(2026, 9, 4), "reminders")
    assert request.call_args_list[0].args == (
        "/v1/queue/publish", "POST",
        {"queue": "reminders", "payload": {"order_id": "order-7", "kind": "handoff", "days_left": 1},
         "idempotency_key": "reminder-order-7"},
    )
    assert request.call_args_list[1].args == (
        "/v1/cron/create", "POST",
        {"cron_expr": "0 9 * * *", "task": "https://example.test/reminders",
         "idempotency_key": "schedule-order-7"},
    )
