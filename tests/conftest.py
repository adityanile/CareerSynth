import importlib
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _install_stub_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    agent_framework = types.ModuleType("agent_framework")

    class DummyAgent:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class DummySkillsProvider:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        @classmethod
        def from_paths(cls, *args, **kwargs):
            return cls(*args, **kwargs)

    class ChatContext:
        def __init__(self):
            self.messages = []

    class ChatMiddleware:
        async def process(self, context, call_next):
            await call_next()

    class Message:
        def __init__(self, role=None, contents=None):
            self.role = role
            self.contents = contents or []
            self.message_id = None
            self.additional_properties = {}

    def tool(fn=None, **kwargs):
        if fn is None:
            def _decorator(inner_fn):
                return inner_fn

            return _decorator
        return fn

    agent_framework.Agent = DummyAgent
    agent_framework.SkillsProvider = DummySkillsProvider
    agent_framework.ChatContext = ChatContext
    agent_framework.ChatMiddleware = ChatMiddleware
    agent_framework.Message = Message
    agent_framework.tool = tool

    agent_framework_openai = types.ModuleType("agent_framework.openai")

    class DummyOpenAIChatClient:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    agent_framework_openai.OpenAIChatClient = DummyOpenAIChatClient
    agent_framework_openai.OpenAIChatCompletionClient = DummyOpenAIChatClient

    agent_framework_ag_ui_submodule = types.ModuleType("agent_framework.ag_ui")

    class DummyAgentFrameworkAgent:
        def __init__(self, agent=None, **kwargs):
            self.agent = agent
            self.kwargs = kwargs

    def add_agent_framework_fastapi_endpoint_submodule(app, agent, route, dependencies=None, **kwargs):
        return None

    agent_framework_ag_ui_submodule.AgentFrameworkAgent = DummyAgentFrameworkAgent
    agent_framework_ag_ui_submodule.add_agent_framework_fastapi_endpoint = add_agent_framework_fastapi_endpoint_submodule
    agent_framework_ag_ui_submodule.state_update = lambda text="", state=None, tool_result=None: {
        "text": text,
        "state": state,
        "tool_result": tool_result,
    }

    agent_framework_ag_ui = types.ModuleType("agent_framework_ag_ui")

    def add_agent_framework_fastapi_endpoint(app, agent, route, **kwargs):
        return None

    agent_framework_ag_ui.add_agent_framework_fastapi_endpoint = add_agent_framework_fastapi_endpoint
    agent_framework_ag_ui.AgentFrameworkAgent = DummyAgentFrameworkAgent

    fastapi_microsoft_identity = types.ModuleType("fastapi_microsoft_identity")

    class AuthError(Exception):
        def __init__(self, error_msg: str):
            super().__init__(error_msg)
            self.error_msg = error_msg

    class TokenAuthService:
        @staticmethod
        def get_token_claims(request):
            oid = request.headers.get("x-test-oid")
            return {"oid": oid} if oid else {}

    def initialize(*args, **kwargs):
        return None

    def requires_auth(fn):
        return fn

    def validate_scope(required_scope, request):
        if request.headers.get("x-force-scope-error") == "1":
            raise AuthError("Missing required scope")
        return None

    fastapi_microsoft_identity.AuthError = AuthError
    fastapi_microsoft_identity.initialize = initialize
    fastapi_microsoft_identity.requires_auth = requires_auth
    fastapi_microsoft_identity.validate_scope = validate_scope
    fastapi_microsoft_identity.auth_service = TokenAuthService
    fastapi_microsoft_identity.authservice = TokenAuthService

    monkeypatch.setitem(sys.modules, "agent_framework", agent_framework)
    monkeypatch.setitem(sys.modules, "agent_framework.openai", agent_framework_openai)
    monkeypatch.setitem(sys.modules, "agent_framework.ag_ui", agent_framework_ag_ui_submodule)
    monkeypatch.setitem(sys.modules, "agent_framework_ag_ui", agent_framework_ag_ui)
    monkeypatch.setitem(sys.modules, "fastapi_microsoft_identity", fastapi_microsoft_identity)


@pytest.fixture
def app_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _install_stub_modules(monkeypatch)
    repo_root = Path(__file__).resolve().parents[1]
    backend_root = repo_root / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    monkeypatch.setenv("ENTRA_TENANT_ID", "tenant")
    monkeypatch.setenv("ENTRA_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "dummy")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.invalid")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "dummy-key")
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "test.db"))

    if "server" in sys.modules:
        del sys.modules["server"]
    server = importlib.import_module("server")
    return server


@pytest.fixture
def client(app_module):
    with TestClient(app_module.app) as test_client:
        yield test_client


@pytest.fixture
def oid_headers():
    def _headers(oid: str = "user-1"):
        return {"x-test-oid": oid}

    return _headers
