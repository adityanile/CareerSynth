import pytest


def test_add_summary_tool_sets_and_overwrites_summary(app_module):
    from agents.context import (
        reset_current_oid,
        reset_current_thread_id,
        set_current_oid,
        set_current_thread_id,
    )
    from agents.tools import resume_state_tools

    resume_state_tools.resume_state_cache.clear()
    resume_state_tools.resume_state_locks.clear()

    oid_token = set_current_oid("user-1")
    thread_token = set_current_thread_id("thread-1")
    try:
        first = resume_state_tools.add_summary_tool("Build reliable backend systems.")
        second = resume_state_tools.add_summary_tool("Lead backend architecture decisions.")
    finally:
        reset_current_thread_id(thread_token)
        reset_current_oid(oid_token)

    assert first["state"] == {"summary": "Build reliable backend systems."}
    assert second["state"] == {"summary": "Lead backend architecture decisions."}
    assert resume_state_tools.resume_state_cache[("user-1", "thread-1")]["summary"] == (
        "Lead backend architecture decisions."
    )


def test_add_summary_tool_rejects_empty_string(app_module):
    from agents.context import (
        reset_current_oid,
        reset_current_thread_id,
        set_current_oid,
        set_current_thread_id,
    )
    from agents.tools import resume_state_tools

    oid_token = set_current_oid("user-1")
    thread_token = set_current_thread_id("thread-1")
    try:
        with pytest.raises(ValueError):
            resume_state_tools.add_summary_tool("   ")
    finally:
        reset_current_thread_id(thread_token)
        reset_current_oid(oid_token)


def test_runtime_includes_summary_predicted_state_config(app_module):
    from agents import runtime

    agent_framework_agent = runtime._build_agent_framework_agent()

    state_schema = agent_framework_agent.kwargs["state_schema"]
    predict_state_config = agent_framework_agent.kwargs["predict_state_config"]
    tools = agent_framework_agent.agent.kwargs["tools"]

    assert state_schema["summary"]["type"] == "string"
    assert predict_state_config["summary"] == {
        "tool": "add_summary",
        "tool_argument": "summary",
    }
    assert any(getattr(tool, "__name__", "") == "add_summary_tool" for tool in tools)


def test_add_profile_tool_sets_profile(app_module):
    from agents.context import (
        reset_current_oid,
        reset_current_thread_id,
        set_current_oid,
        set_current_thread_id,
    )
    from agents.tools import resume_state_tools

    resume_state_tools.resume_state_cache.clear()
    resume_state_tools.resume_state_locks.clear()

    oid_token = set_current_oid("user-1")
    thread_token = set_current_thread_id("thread-1")
    try:
        result = resume_state_tools.add_profile_tool(
            {
                "name": "Aditya",
                "role": "Software Engineer",
                "contact": "aditya@example.com",
                "location": "Bengaluru, India",
                "linkedinurl": "https://linkedin.com/in/aditya",
                "additionalUrls": ["https://github.com/aditya", "https://portfolio.example.com"],
            }
        )
    finally:
        reset_current_thread_id(thread_token)
        reset_current_oid(oid_token)

    assert result["state"]["profile"] == {
        "name": "Aditya",
        "role": "Software Engineer",
        "contact": "aditya@example.com",
        "location": "Bengaluru, India",
        "linkedinUrl": "https://linkedin.com/in/aditya",
        "additionalUrls": ["https://github.com/aditya", "https://portfolio.example.com"],
    }


def test_add_profile_tool_rejects_missing_required_fields(app_module):
    from agents.context import (
        reset_current_oid,
        reset_current_thread_id,
        set_current_oid,
        set_current_thread_id,
    )
    from agents.tools import resume_state_tools

    oid_token = set_current_oid("user-1")
    thread_token = set_current_thread_id("thread-1")
    try:
        with pytest.raises(ValueError):
            resume_state_tools.add_profile_tool(
                {
                    "name": "Aditya",
                    "role": "",
                    "contact": "aditya@example.com",
                    "location": "Bengaluru, India",
                    "linkedinUrl": "https://linkedin.com/in/aditya",
                    "additionalUrls": [],
                }
            )
    finally:
        reset_current_thread_id(thread_token)
        reset_current_oid(oid_token)


def test_runtime_includes_profile_predicted_state_config(app_module):
    from agents import runtime

    agent_framework_agent = runtime._build_agent_framework_agent()

    state_schema = agent_framework_agent.kwargs["state_schema"]
    predict_state_config = agent_framework_agent.kwargs["predict_state_config"]
    tools = agent_framework_agent.agent.kwargs["tools"]

    assert state_schema["profile"]["type"] == "object"
    assert predict_state_config["profile"] == {
        "tool": "add_profile",
        "tool_argument": "profile",
    }
    assert any(getattr(tool, "__name__", "") == "add_profile_tool" for tool in tools)


def test_add_skills_tool_sets_skills(app_module):
    from agents.context import (
        reset_current_oid,
        reset_current_thread_id,
        set_current_oid,
        set_current_thread_id,
    )
    from agents.tools import resume_state_tools

    resume_state_tools.resume_state_cache.clear()
    resume_state_tools.resume_state_locks.clear()

    oid_token = set_current_oid("user-1")
    thread_token = set_current_thread_id("thread-1")
    try:
        result = resume_state_tools.add_skills_tool(["Python", "FastAPI", "Azure"])
    finally:
        reset_current_thread_id(thread_token)
        reset_current_oid(oid_token)

    assert result["state"] == {"skills": ["Python", "FastAPI", "Azure"]}


def test_add_skills_tool_rejects_empty_input(app_module):
    from agents.context import (
        reset_current_oid,
        reset_current_thread_id,
        set_current_oid,
        set_current_thread_id,
    )
    from agents.tools import resume_state_tools

    oid_token = set_current_oid("user-1")
    thread_token = set_current_thread_id("thread-1")
    try:
        with pytest.raises(ValueError):
            resume_state_tools.add_skills_tool([])
    finally:
        reset_current_thread_id(thread_token)
        reset_current_oid(oid_token)


def test_runtime_includes_skills_predicted_state_config(app_module):
    from agents import runtime

    agent_framework_agent = runtime._build_agent_framework_agent()

    state_schema = agent_framework_agent.kwargs["state_schema"]
    predict_state_config = agent_framework_agent.kwargs["predict_state_config"]
    tools = agent_framework_agent.agent.kwargs["tools"]

    assert state_schema["skills"]["type"] == "array"
    assert predict_state_config["skills"] == {
        "tool": "add_skills",
        "tool_argument": "skills",
    }
    assert any(getattr(tool, "__name__", "") == "add_skills_tool" for tool in tools)


def test_add_education_to_resume_tool_sets_education_list(app_module):
    from agents.context import (
        reset_current_oid,
        reset_current_thread_id,
        set_current_oid,
        set_current_thread_id,
    )
    from agents.tools import resume_state_tools

    resume_state_tools.resume_state_cache.clear()
    resume_state_tools.resume_state_locks.clear()

    oid_token = set_current_oid("user-1")
    thread_token = set_current_thread_id("thread-1")
    try:
        result = resume_state_tools.add_education_to_resume_tool(
            {
                "degreeName": "B.Tech Computer Science",
                "location": "Bengaluru",
                "startYear": "2020",
                "endYear": "2024",
                "cgpaOrPercentage": "8.6 CGPA",
            }
        )
    finally:
        reset_current_thread_id(thread_token)
        reset_current_oid(oid_token)

    assert len(result["state"]["educations"]) == 1
    assert result["state"]["educations"][0]["degreeName"] == "B.Tech Computer Science"


def test_runtime_includes_educations_predicted_state_config(app_module):
    from agents import runtime

    agent_framework_agent = runtime._build_agent_framework_agent()

    state_schema = agent_framework_agent.kwargs["state_schema"]
    predict_state_config = agent_framework_agent.kwargs["predict_state_config"]
    tools = agent_framework_agent.agent.kwargs["tools"]

    assert state_schema["educations"]["type"] == "array"
    assert predict_state_config["educations"] == {
        "tool": "add_education_to_resume",
        "tool_argument": "education",
    }
    assert any(getattr(tool, "__name__", "") == "add_education_to_resume_tool" for tool in tools)
