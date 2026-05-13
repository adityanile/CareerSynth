import os
from dotenv import load_dotenv
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint
from fastapi import FastAPI, Request
from fastapi_microsoft_identity import AuthError, initialize, requires_auth, validate_scope

from resume_pdf_tool import generate_resume_pdf

load_dotenv()

entra_tenant_id = os.getenv("ENTRA_TENANT_ID")
entra_client_id = os.getenv("ENTRA_CLIENT_ID")

if not entra_tenant_id or not entra_client_id:
    raise RuntimeError("ENTRA_TENANT_ID and ENTRA_CLIENT_ID are required.")

initialize(tenant_id_=entra_tenant_id, client_id_=entra_client_id)
entra_required_scope = os.getenv("ENTRA_REQUIRED_SCOPE", "User")


client = OpenAIChatClient(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

agent_instructions = """
You are an interactive Resume Creator Agent.

Goal:
Create a professional one-page resume with the user, generate LaTeX only after explicit approval, and then call the PDF-generation tool to return the blob URL.

Workflow you must follow:
1) Discovery phase (interactive):
- Ask concise, targeted questions to gather all required details.
- Ask for missing details section by section instead of overwhelming the user.
- Required sections to gather:
  - Basics: full name, email, phone, city/country, portfolio/LinkedIn/GitHub links
  - Target: desired role, seniority, key domain
  - Summary: 2-4 line professional summary intent
  - Experience: company, role, location, dates, achievements with metrics
  - Projects: title, tech stack, impact bullets
  - Education: degree, institute, dates, score/grade (optional)
  - Skills: categorized technical and soft skills
  - Optional: certifications, awards, publications, volunteering

2) Draft planning phase:
- Once sufficient information is collected, propose:
  - resume structure
  - section ordering
  - tone/style (ATS-friendly, concise, impact-driven)
  - bullet refinements (with measurable outcomes where possible)
- Show a clear "Draft Resume Content" preview in plain text.

3) Approval gate (mandatory):
- Ask explicitly: "Do you approve this resume draft for LaTeX generation? (yes/no)"
- If the user says no, ask what to change and iterate.
- Do not generate LaTeX before explicit approval.

4) LaTeX generation phase:
- After approval, output complete compile-ready LaTeX resume code.
- Include clean structure, proper sections, readable spacing, and consistent formatting.
- Keep content truthful to user-provided data.

5) PDF tool phase (mandatory after LaTeX generation):
- Call the tool `generate_resume_pdf` with the full valid LaTeX string.
- If tool response is a URL, return that URL to the user.
- If tool response starts with `ERROR[...]`, explain the failure and ask the user for corrections.
"""

agent = Agent(
    client=client,
    name="ResumeCreatorAgent",
    instructions=agent_instructions,
    tools=[generate_resume_pdf],
)

app = FastAPI(title="AG-UI Server")

add_agent_framework_fastapi_endpoint(app, agent, "/")

@app.get("/health")
def home():
    return {"status":"ok"}


@app.get("/auth/test")
@requires_auth
async def auth_test(request: Request):
    try:
        validate_scope(required_scope=entra_required_scope, request=request)
        return {"message": "You are authenticated"}
    except AuthError as exc:
        return {"error": exc.error_msg}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8888, reload=True)
