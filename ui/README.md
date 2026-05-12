## CareerSynth Agent UI

This frontend provides a multi-conversation chat UI for your existing AG-UI backend (Microsoft Agent Framework + `agent_framework_ag_ui`).

It includes:

- Copilot Runtime API route (`/api/copilotkit/:integrationId`) that proxies to your AG-UI agent
- Chat interface with `CopilotChat`
- Thread sidebar using `useThreads` (select/new/rename/archive + pagination)
- Persistent thread support when configured with Copilot Cloud/Intelligence public key

## 1. Configure environment

Copy the example and fill values:

```bash
cp .env.example .env.local
```

Key variables:

- `COPILOT_DEFAULT_INTEGRATION_ID`: default UI route (redirect target from `/`)
- `AG_UI_AGENT_URL`: URL for your running AG-UI backend (default: `http://127.0.0.1:8888/`)
- `COPILOT_AGENT_ID` and `NEXT_PUBLIC_COPILOT_AGENT_ID`: runtime/UI agent IDs (if unset on UI, it falls back to `integrationId`)
- `NEXT_PUBLIC_COPILOT_PUBLIC_API_KEY` (or `NEXT_PUBLIC_COPILOT_PUBLIC_LICENSE_KEY`): required for cross-session persistent threads on Copilot Cloud/Intelligence

Optional per-integration overrides are also supported:

- `AG_UI_AGENT_URL_<INTEGRATION_ID>`
- `COPILOT_AGENT_ID_<INTEGRATION_ID>`

## 2. Run backend and frontend

Start your Python AG-UI backend from repo root:

```bash
python server.py
```

Then run this UI:

```bash
npm install
npm run dev
```

Open `http://localhost:3000` (it redirects to `/<COPILOT_DEFAULT_INTEGRATION_ID>`).

## 3. Architecture

- `src/app/api/copilotkit/[integrationId]/route.ts`: Copilot Runtime + `HttpAgent` bridge to AG-UI.
- `src/components/agentic-chat.tsx`: CopilotKit provider with dynamic runtime URL (`/api/copilotkit/${integrationId}`).
- `src/components/multi-conversation-chat.tsx`: thread sidebar and chat panel.

## Notes

- Without a Copilot public key, chat still works, but persistent multi-session thread history will not be available.
