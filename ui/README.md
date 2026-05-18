## CareerSynth Agent UI

This frontend provides a multi-conversation chat UI for your existing AG-UI backend (Microsoft Agent Framework + `agent_framework_ag_ui`).

It includes:

- Copilot Runtime API route (`/api/copilotkit`) that proxies to your AG-UI agent
- Chat interface with `CopilotChat`
- Thread sidebar using `useThreads` (select/new/rename/archive + pagination)
- Shared resume state panel (projects, experiences, achievements) rendered from AG-UI state
- In-app shared-state editing from frontend via `useAgent(...).agent.setState(...)` (add/edit/delete)
- Persistent thread support when configured with Copilot Cloud/Intelligence public key

## 1. Configure environment

Copy the example and fill values:

```bash
cp .env.example .env.local
```

Key variables:

- `COPILOT_DEFAULT_INTEGRATION_ID`: default integration id used by backend/runtime config
- `AG_UI_AGENT_URL`: URL for your running AG-UI backend (default: `http://127.0.0.1:8888/`)
- `COPILOT_AGENT_ID` and `NEXT_PUBLIC_COPILOT_AGENT_ID`: runtime/UI agent IDs (if unset on UI, it falls back to `integrationId`)
- `NEXT_PUBLIC_COPILOT_PUBLIC_API_KEY` (or `NEXT_PUBLIC_COPILOT_PUBLIC_LICENSE_KEY`): required for cross-session persistent threads on Copilot Cloud/Intelligence
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY`: required for Clerk auth
- `CLERK_AUTH_REQUIRED`: when `true`, runtime API routes reject requests that don't have an `Authorization: Bearer <token>` header

Optional per-integration overrides are also supported:

- `AG_UI_AGENT_URL_<INTEGRATION_ID>`
- `COPILOT_AGENT_ID_<INTEGRATION_ID>`

## 1.1 Clerk setup checklist

1. Create a Clerk application and copy keys from the Clerk dashboard.
2. Set `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` in `.env.local`.
3. Keep `CLERK_AUTH_REQUIRED=true` for protected runtime routes.
4. Start the UI and complete sign-up/sign-in from the Clerk auth UI.

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

Open `http://localhost:3000`.

## 3. Shared Resume State Contract

The UI expects the AG-UI state shape:

```json
{
  "projects": [],
  "experiences": [],
  "achievements": [],
  "educations": [],
  "summary": "",
  "skills": [],
  "profile": {
    "name": "",
    "role": "",
    "contact": "",
    "location": "",
    "linkedinUrl": "",
    "additionalUrls": []
  }
}
```

Current backend pattern (in `server.py` + `resume_state_tools.py`) uses:

- `add_project_to_resume` with argument `projects` (array)
- `add_experience_to_resume` with argument `experiences` (array)
- `add_achievement_to_resume` with argument `achievements` (array)
- `add_education_to_resume` with argument `educations` (array)
- `add_summary` with argument `summary` (string)
- `add_skills` with argument `skills` (string[])
- `add_profile` with argument `profile` (object)

These tools append list items to backend-maintained shared state and stream updates via AG-UI.

## 4. Architecture

- `src/app/api/copilotkit/route.ts`: Copilot Runtime + `HttpAgent` bridge to AG-UI.
- `src/components/agentic-chat.tsx`: CopilotKit provider using `/api/copilotkit`.
- `src/components/multi-conversation-chat.tsx`: thread sidebar, chat panel, and shared-state editor panel.

## Notes

- Without a Copilot public key, chat still works, but persistent multi-session thread history will not be available.
- The `/redirect` page is a plain fallback route and is not required for Clerk auth flows.
