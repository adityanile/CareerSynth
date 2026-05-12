import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Annotated

from agent_framework import tool
from azure.storage.blob import BlobServiceClient, ContentSettings


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _validate_latex_input(latex_code: str) -> tuple[bool, str]:
    content = latex_code.strip()
    if not content:
        return False, "LaTeX input cannot be empty."

    if len(content) > 200_000:
        return False, "LaTeX input is too large (max 200000 characters)."

    required_patterns = [
        r"\\documentclass(?:\[[^\]]*\])?\{[^}]+\}",
        r"\\begin\{document\}",
        r"\\end\{document\}",
    ]
    for pattern in required_patterns:
        if not re.search(pattern, content, flags=re.DOTALL):
            return False, "Invalid LaTeX structure. Expected documentclass and document environment."

    if content.count("\\begin{document}") != content.count("\\end{document}"):
        return False, "Mismatched \\begin{document} and \\end{document}."

    if "\x00" in content:
        return False, "Invalid null-byte character found in input."

    return True, ""


def _upload_pdf_to_blob(pdf_bytes: bytes, blob_name: str) -> str:
    account_name = _required_env("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = _required_env("AZURE_STORAGE_ACCOUNT_KEY")
    container_name = _required_env("AZURE_STORAGE_CONTAINER_NAME")

    account_url = f"https://{account_name}.blob.core.windows.net"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=account_key)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(
        pdf_bytes,
        overwrite=True,
        content_settings=ContentSettings(
            content_type="application/pdf",
            content_disposition="inline",
        ),
    )

    props = blob_client.get_blob_properties()
    if props.size != len(pdf_bytes):
        raise RuntimeError(
            f"Blob upload size mismatch. expected={len(pdf_bytes)} actual={props.size}"
        )
    return blob_client.url


@tool(name="generate_resume_pdf",description="Use This Tool To Generate PDF of the Resume From Latex source")
def generate_resume_pdf(
    latex_code: Annotated[str, "Complete valid LaTeX source for the resume document."]
) -> str:
    """Compile LaTeX resume code into PDF, upload to Azure Blob, and return blob URL."""
    valid, validation_error = _validate_latex_input(latex_code)
    if not valid:
        return f"ERROR[validation]: {validation_error}"

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            tex_path = tmp_path / "resume.tex"
            pdf_path = tmp_path / "resume.pdf"

            tex_path.write_text(latex_code, encoding="utf-8")

            completed = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    f"-output-directory={tmp_path}",
                    str(tex_path),
                ],
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                error_text = (completed.stderr or completed.stdout or "").strip()
                return f"ERROR[compile]: LaTeX compilation failed. {error_text[:4000]}"

            if not pdf_path.exists():
                return "ERROR[compile]: Compilation succeeded but PDF was not generated."

            pdf_bytes = pdf_path.read_bytes()
            if not pdf_bytes:
                return "ERROR[compile]: Generated PDF is empty."

            blob_name = f"{uuid.uuid4()}.pdf"
            blob_url = _upload_pdf_to_blob(pdf_bytes, blob_name)
            if not blob_url:
                return "ERROR[upload]: Blob upload completed but URL is empty."

            return blob_url
    except Exception as exc:
        return f"ERROR[runtime]: {exc}"
