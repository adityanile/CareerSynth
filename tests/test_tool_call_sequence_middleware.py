from types import SimpleNamespace


def _content(content_type: str, call_id: str | None = None):
    return SimpleNamespace(type=content_type, call_id=call_id)


async def _run_middleware(middleware, context):
    called = {"value": False}

    async def call_next():
        called["value"] = True

    await middleware.process(context, call_next)
    assert called["value"] is True


def test_middleware_supports_parallel_tool_calls_with_batched_results(app_module):
    from agent_framework import ChatContext, Message
    from agents.middleware.tool_call_sequence_middleware import ToolCallSequenceRepairMiddleware

    context = ChatContext()
    assistant = Message(
        role="assistant",
        contents=[
            _content("function_call", "call-1"),
            _content("function_call", "call-2"),
        ],
    )
    tool = Message(
        role="tool",
        contents=[
            _content("function_result", "call-1"),
            _content("function_result", "call-2"),
        ],
    )
    context.messages = [assistant, tool]

    middleware = ToolCallSequenceRepairMiddleware()

    import asyncio

    asyncio.run(_run_middleware(middleware, context))

    assert len(context.messages) == 3
    assert context.messages[0].role == "assistant"
    assert [c.call_id for c in context.messages[0].contents if c.type == "function_call"] == ["call-1", "call-2"]
    assert context.messages[1].role == "tool"
    assert [c.call_id for c in context.messages[1].contents if c.type == "function_result"] == ["call-1"]
    assert context.messages[2].role == "tool"
    assert [c.call_id for c in context.messages[2].contents if c.type == "function_result"] == ["call-2"]


def test_middleware_matches_mixed_tool_result_layouts(app_module):
    from agent_framework import ChatContext, Message
    from agents.middleware.tool_call_sequence_middleware import ToolCallSequenceRepairMiddleware

    context = ChatContext()
    assistant = Message(
        role="assistant",
        contents=[
            _content("function_call", "call-a"),
            _content("function_call", "call-b"),
            _content("function_call", "call-c"),
        ],
    )
    tool_batched = Message(
        role="tool",
        contents=[
            _content("function_result", "call-c"),
            _content("function_result", "call-a"),
        ],
    )
    tool_single = Message(
        role="tool",
        contents=[_content("function_result", "call-b")],
    )
    context.messages = [assistant, tool_batched, tool_single]

    middleware = ToolCallSequenceRepairMiddleware()

    import asyncio

    asyncio.run(_run_middleware(middleware, context))

    assert len(context.messages) == 4
    assert context.messages[0].role == "assistant"
    assert [c.call_id for c in context.messages[1].contents if c.type == "function_result"] == ["call-a"]
    assert [c.call_id for c in context.messages[2].contents if c.type == "function_result"] == ["call-b"]
    assert [c.call_id for c in context.messages[3].contents if c.type == "function_result"] == ["call-c"]
