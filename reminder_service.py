from dataclasses import dataclass
from datetime import date
from typing import Any

from infrai_client import InfraiClient


@dataclass(frozen=True)
class MarketplaceDeadline:
    order_id: str
    asset_ready: bool
    buyer_updated: bool
    handoff_due: date


def reminder_for(item: MarketplaceDeadline, today: date) -> dict[str, Any] | None:
    """Return one handoff reminder when the seller is ready and the deadline is near."""
    days_left = (item.handoff_due - today).days
    if item.asset_ready and item.buyer_updated and 0 <= days_left <= 2:
        return {"order_id": item.order_id, "kind": "handoff", "days_left": days_left}
    return None


def schedule_deadline(item: MarketplaceDeadline, webhook: str, client: InfraiClient, today: date, queue: str) -> dict[str, Any] | None:
    reminder = reminder_for(item, today)
    if reminder is None:
        return None
    client.queue_publish(queue, reminder, request_id=f"reminder-{item.order_id}")
    return client.cron_create("0 9 * * *", webhook, request_id=f"schedule-{item.order_id}")


if __name__ == "__main__":
    from os import environ

    sample = MarketplaceDeadline("order-1042", True, True, date.today())
    result = schedule_deadline(sample, environ["REMINDER_WEBHOOK_URL"], InfraiClient(), date.today(), environ["REMINDER_QUEUE"])
    print({"scheduled": result is not None, "job_id": (result or {}).get("job_id")})
