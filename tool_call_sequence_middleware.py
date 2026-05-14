from __future__ import annotations

from collections.abc import Awaitable, Callable

from agent_framework import ChatContext, ChatMiddleware, Message


def _role_value(message: Message) -> str:
    role = getattr(message, "role", "")
    return role.value if hasattr(role, "value") else str(role)


def _assistant_call_ids(message: Message) -> list[str]:
    ids: list[str] = []
    for content in message.contents or []:
        if content.type == "function_call" and content.call_id:
            ids.append(str(content.call_id))
    return ids


def _tool_result_id(message: Message) -> str | None:
    for content in message.contents or []:
        if content.type == "function_result" and content.call_id:
            return str(content.call_id)
    return None


def _dedupe_by_message_id(messages: list[Message]) -> list[Message]:
    seen: set[str] = set()
    result: list[Message] = []
    for msg in messages:
        message_id = getattr(msg, "message_id", None)
        if message_id:
            if message_id in seen:
                continue
            seen.add(message_id)
        result.append(msg)
    return result


def _filter_assistant_calls_by_matched_results(message: Message, matched_call_ids: set[str]) -> Message | None:
    filtered_contents = []
    for content in message.contents or []:
        if content.type != "function_call":
            filtered_contents.append(content)
            continue
        if content.call_id and str(content.call_id) in matched_call_ids:
            filtered_contents.append(content)

    if not filtered_contents:
        return None

    filtered = Message(role=message.role, contents=filtered_contents)
    filtered.message_id = message.message_id
    filtered.additional_properties = dict(message.additional_properties or {})
    return filtered


class ToolCallSequenceRepairMiddleware(ChatMiddleware):
    """Normalize chat history so tool-call blocks are always provider-valid.

    Strategy:
    - Keep assistant function_call entries only when a matching tool result exists.
    - Drop unmatched function_call entries instead of injecting synthetic tool outputs.
    - Drop orphan tool messages outside assistant tool-call blocks.
    - Preserve normal user/assistant text messages unchanged.
    """

    async def process(
        self,
        context: ChatContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        messages = _dedupe_by_message_id(list(context.messages))
        # Capture first tool-result message per call_id from anywhere in history.
        # We later re-attach these results immediately after the matching assistant call.
        tool_result_by_call_id: dict[str, Message] = {}
        for msg in messages:
            if _role_value(msg) != "tool":
                continue
            call_id = _tool_result_id(msg)
            if not call_id:
                continue
            if call_id not in tool_result_by_call_id:
                tool_result_by_call_id[call_id] = msg

        normalized: list[Message] = []
        consumed_call_ids: set[str] = set()

        for msg in messages:
            role = _role_value(msg)
            if role == "tool":
                # We reinsert tool results in canonical position after assistant call.
                continue

            if role != "assistant":
                normalized.append(msg)
                continue

            assistant_call_ids = _assistant_call_ids(msg)
            if not assistant_call_ids:
                normalized.append(msg)
                continue

            matched_call_ids = {
                call_id for call_id in assistant_call_ids if call_id in tool_result_by_call_id and call_id not in consumed_call_ids
            }
            filtered_assistant = _filter_assistant_calls_by_matched_results(msg, matched_call_ids)
            if filtered_assistant is None:
                continue

            normalized.append(filtered_assistant)
            for call_id in assistant_call_ids:
                if call_id in matched_call_ids:
                    normalized.append(tool_result_by_call_id[call_id])
                    consumed_call_ids.add(call_id)

        context.messages = normalized
        await call_next()
