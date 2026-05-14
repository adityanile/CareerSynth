def format_tool_failure(tool_name: str, error: str) -> str:
    normalized = " ".join(str(error).split())
    return f"TOOL_CALL_FAILED|tool={tool_name}|error={normalized}"
