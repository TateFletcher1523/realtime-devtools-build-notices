import pytest

from src.devtools_notifications import BuildEvent, notification_for, publish_build


def test_failed_build_requires_attention():
    notice = notification_for(BuildEvent("search-api", "abc123", "failed", "mina"))
    assert notice["status"] == "failed"
    assert notice["message"] == "Build needs attention for search-api"


def test_unknown_status_is_rejected():
    with pytest.raises(ValueError):
        notification_for(BuildEvent("search-api", "abc123", "running", "mina"))


def test_publish_build_does_not_create_persistent_channel():
    class Realtime:
        def create_channel(self, channel):
            pytest.fail("publish_build must not create a persistent channel")

        def publish(self, channel, event, data, account_id):
            assert channel == "devtools-search-api"
            assert event == "build.completed"
            assert account_id == "developer-tools"
            return {"ok": True, "data": data}

    result = publish_build(Realtime(), BuildEvent("search-api", "abc123", "succeeded", "mina"), "developer-tools")
    assert result["data"]["status"] == "succeeded"
