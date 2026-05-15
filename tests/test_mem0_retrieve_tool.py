import sys
import types


def test_retrieve_tool_searches_mem0_with_user_scope(app_module, monkeypatch):
    from agents.tools import mem0_retrieve_tool

    captured: dict[str, object] = {}

    class _FakeMemoryClient:
        def __init__(self, api_key: str):
            captured["api_key"] = api_key

        def search(self, query: str, filters):
            captured["query"] = query
            captured["filters"] = filters
            return [{"memory": "Prefers backend and distributed systems."}]

    fake_mem0 = types.SimpleNamespace(MemoryClient=_FakeMemoryClient)
    monkeypatch.setitem(sys.modules, "mem0", fake_mem0)
    monkeypatch.setattr(mem0_retrieve_tool, "require_current_oid", lambda: "user-1")

    result = mem0_retrieve_tool.retrieve_from_mem0_tool("What do you know about me?")

    assert result["ok"] is True
    assert result["data"]["items"][0]["memory"] == "Prefers backend and distributed systems."
    assert captured["query"] == "What do you know about me?"
    assert captured["filters"] == {"user_id": "user-1"}
