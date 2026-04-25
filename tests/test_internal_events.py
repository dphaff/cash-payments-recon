from decimal import Decimal

import pytest

from cash_recon.io.internal_events import load_internal_events


def test_load_valid_internal_events():
    events = load_internal_events("examples/internal_events_valid.csv")

    assert len(events) == 4

    first_event = events[0]

    assert first_event.event_id == "INT001"
    assert first_event.merchant_reference == "ORDER-1001"
    assert first_event.event_type == "PAYMENT"
    assert first_event.gross_amount == Decimal("25.00")
    assert first_event.currency == "GBP"


def test_invalid_internal_events_file_raises_error():
    with pytest.raises(ValueError):
        load_internal_events("examples/internal_events_invalid.csv")