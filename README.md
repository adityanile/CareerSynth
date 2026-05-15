# CareerSynth

CareerSynth is a resume creation system built on the Microsoft Agent Framework + AG-UI.

It includes:
- A backend Resume Creator agent (`backend/server.py`)
- A tool that compiles LaTeX resumes to PDF and uploads to Azure Blob (`backend/agents/tools/resume_pdf_tool.py`)
- A helper CLI compiler/uploader script (`compile_tex.py`)
- A Next.js chat UI (`ui/`)

## Project Structure

- `backend/server.py`: backend entrypoint for FastAPI + AG-UI endpoint.
- `backend/app.py`: app composition (routers, auth/OpenAPI wiring, startup).
- `backend/agents/tools/resume_pdf_tool.py`: `@tool()` implementation `generate_resume_pdf(...)`.
- `compile_tex.py`: CLI utility to compile a local `.tex` file and upload the resulting PDF.
- `docker/backend.dockerfile`: Backend image with Python + TeX Live + dependencies.
- `docker/requirements.txt`: Backend Python dependencies.
- `ui/`: Frontend app.

## How The Agent Works

1. Interactively collects resume details from the user.
2. Produces a draft and asks for explicit approval.
3. Generates final LaTeX only after approval.
4. Calls `generate_resume_pdf` tool with the LaTeX.
5. Tool compiles PDF, uploads to Azure Blob with UUID filename, returns blob URL.

## Tool Behavior (`generate_resume_pdf`)

Input:
- `latex_code` (string): full LaTeX source.

Validation:
- non-empty input
- max size check
- requires `\documentclass`, `\begin{document}`, `\end{document}`
- checks begin/end document balance
- rejects null-byte input

Execution:
- compiles using `pdflatex` in a temp directory
- verifies generated PDF exists and is non-empty
- uploads to Azure Blob
- sets blob content headers for browser viewing:
  - `content_type=application/pdf`
  - `content_disposition=inline`
- validates upload with blob property size check

Return format:
- success: blob URL (string)
- failure: string with `ERROR[validation]`, `ERROR[compile]`, `ERROR[upload]`, or `ERROR[runtime]`

## Environment Variables

Create a `.env` in project root for backend:

```env
# Azure OpenAI (agent model)
AZURE_OPENAI_DEPLOYMENT=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...

# Azure Blob Storage (PDF upload)
AZURE_STORAGE_ACCOUNT_NAME=...
AZURE_STORAGE_ACCOUNT_KEY=...
AZURE_STORAGE_CONTAINER_NAME=...

# Entra auth for backend
ENTRA_TENANT_ID=...
ENTRA_CLIENT_ID=...
ENTRA_REQUIRED_SCOPE=User
# Optional: comma-separated tenant allow-list (if unset, all tenants accepted)
# ENTRA_ALLOWED_TENANTS=<tenant-guid-1>,<tenant-guid-2>

# Optional: SQLite path
SQLITE_DB_PATH=careersynth.db
```

## CRUD API (JWT Protected)

All endpoints below require a valid bearer token with cryptographic JWT validation.
User isolation is enforced with the verified `oid` claim from JWT.

Validation behavior:
- Signature verification uses Microsoft Entra JWKS (resolved by token `tid`, with `common` fallback).
- Audience must match `ENTRA_CLIENT_ID` or `api://ENTRA_CLIENT_ID`.
- Issuer must match tenant-aware Entra patterns:
  - `https://login.microsoftonline.com/{tid}/v2.0` (or trailing slash)
  - `https://sts.windows.net/{tid}/` for v1 tokens
- Required permission check uses `ENTRA_REQUIRED_SCOPE` against token `scp` or `roles`.
- Optional tenant restriction is controlled by `ENTRA_ALLOWED_TENANTS`.

Expected token claims:
- `tid`: tenant id (used for key discovery and issuer checks)
- `oid`: object id (used for per-user data isolation)
- `scp` or `roles`: permission required by `ENTRA_REQUIRED_SCOPE`
- `aud`, `iss`, `exp`: standard JWT claims used in validation

Swagger/OpenAPI:
- `GET /docs` exposes an `Authorize` button with `BearerAuth` (JWT).
- Use value format: `Bearer <access_token>`.

Base resources:
- `/api/projects`
- `/api/experiences`
- `/api/achievements`

Shared operations:
- `POST /api/<resource>` create
- `GET /api/<resource>` list (user-scoped)
- `GET /api/<resource>/{id}` get one (user-scoped)
- `PATCH /api/<resource>/{id}` partial update (user-scoped)
- `DELETE /api/<resource>/{id}` hard delete (user-scoped)

Project-specific filters:
- `GET /api/projects/by-tag/{tag}`
- `GET /api/projects/by-tech/{tech}`
- `GET /api/projects?tag=react`
- `GET /api/projects?tags=react,fastapi` (requires all listed tags)
- `GET /api/projects?tech=python`
- `GET /api/projects?techs=python,fastapi` (requires all listed tech values)
- `GET /api/projects?name=CareerSynth%20Platform`

Experience-specific filters:
- `GET /api/experiences?position=Software%20Engineer`
- `GET /api/experiences/by-position/{position}`
- `GET /api/experiences/by-company/{company_name}`

Achievement-specific filters:
- `GET /api/achievements?organisation=Microsoft`
- `GET /api/achievements?name=Hackathon%20Winner`
- `GET /api/achievements/by-organisation/{organisation}`
- `GET /api/achievements/by-name/{name}`

### Request Shapes

`POST /api/projects`
```json
{
  "name": "CareerSynth Platform",
  "techStack": ["FastAPI", "SQLite", "Next.js"],
  "urls": ["https://example.com"],
  "description": "Resume platform backend",
  "tags": ["backend", "api"]
}
```

`POST /api/experiences`
```json
{
  "companyName": "Acme Corp",
  "startDate": "10-01-2024",
  "endDate": null,
  "position": "Backend Engineer",
  "description": "Built scalable services",
  "location": "Bengaluru"
}
```

`POST /api/achievements`
```json
{
  "name": "Hackathon Winner",
  "link": "https://example.com/certificate",
  "organisation": "Acme",
  "date": "01-12-2025"
}
```

Date field behavior:
- `startDate`, `endDate`, and `date` are stored as user-provided strings.
- `endDate` can be `null` for ongoing roles.

## Local Backend Setup

Install system dependencies (Ubuntu example):

```bash
sudo apt update
sudo apt install -y \
  python3 python3-pip \
  texlive-latex-recommended texlive texlive-fonts-recommended \
  texlive-latex-extra texlive-fonts-extra texlive-lang-all
```

Install Python dependencies:

```bash
pip install -r docker/requirements.txt
```

Run backend:

```bash
python backend/server.py
```

Backend starts on:
- `http://0.0.0.0:8888/`

## API Smoke Test

After backend is running, execute the CRUD smoke test:

```bash
TOKEN="<jwt_access_token>" ./smoke_test_api.sh
```

Optional:
- `BASE_URL=http://localhost:8888` (default)

Prerequisite:
- `jq` installed (used for response parsing)

## CLI Compile/Upload (without agent)

```bash
python compile_tex.py /path/to/resume.tex
```

This compiles the `.tex`, uploads resulting PDF to Blob, prints URL.

## Frontend (UI)

From `ui/`:

```bash
npm install
npm run dev
```

See UI-specific setup in:
- [ui/README.md](/home/aditya/Development/Current_Projects/CareerSynth/ui/README.md)

## Docker Backend

Build image from project root:

```bash
docker build -f docker/backend.dockerfile -t careersynth-backend .
```

Run container:

```bash
docker run --rm -p 8888:8888 --env-file .env careersynth-backend
```

Note:
- Ensure your Dockerfile copies application code into `/app` before runtime if needed.
