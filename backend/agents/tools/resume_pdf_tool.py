import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Annotated

from agent_framework import tool
from azure.storage.blob import BlobServiceClient, ContentSettings
from agents.tools.tool_response import format_tool_failure

COMPILE_TIMEOUT_SECONDS = 45
MAX_ERROR_CHARS = 4000


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


def _normalize_latex_input(latex_code: str) -> str:
    """Normalize common Unicode punctuation that frequently breaks pdflatex."""
    replacements = {
        "\u2013": "--",  # en dash
        "\u2014": "--",  # em dash
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\u2026": "...",  # ellipsis
        "\u00a0": " ",  # non-breaking space
        "\u200b": "",  # zero-width space
        "\ufeff": "",  # BOM
    }

    normalized = latex_code
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


def _extract_latex_error(output: str, log_output: str = "") -> str:
    """Return the most useful LaTeX error context from compiler or .log output."""
    primary = log_output if log_output.strip() else output
    if not primary.strip():
        return "Unknown LaTeX compiler failure."

    lines = primary.splitlines()
    error_indices = [idx for idx, line in enumerate(lines) if line.lstrip().startswith("!")]
    if not error_indices:
        file_line_matches = [
            idx for idx, line in enumerate(lines) if re.search(r"\.tex:\d+:", line)
        ]
        if file_line_matches:
            idx = file_line_matches[0]
            start = max(0, idx - 3)
            end = min(len(lines), idx + 8)
            return "\n".join(lines[start:end]).strip()
        return primary[-MAX_ERROR_CHARS:].strip()

    idx = error_indices[0]
    start = max(0, idx - 3)
    end = min(len(lines), idx + 8)
    return "\n".join(lines[start:end]).strip()


def _escape_unescaped_char(text: str, char: str) -> str:
    return re.sub(rf"(?<!\\){re.escape(char)}", rf"\\{char}", text)


def _repair_common_latex_text_issues(latex_code: str) -> str:
    """Repair common unescaped text chars in resume body and keep structure intact."""
    lines = latex_code.splitlines()
    repaired_lines: list[str] = []
    in_document = False
    in_tabular = 0

    for line in lines:
        if r"\begin{document}" in line:
            in_document = True

        if r"\begin{tabular}" in line or r"\begin{tabular*}" in line:
            in_tabular += 1

        updated_line = line
        if in_document and in_tabular == 0:
            updated_line = _escape_unescaped_char(updated_line, "#")
            updated_line = _escape_unescaped_char(updated_line, "&")

        repaired_lines.append(updated_line)

        if r"\end{tabular}" in line or r"\end{tabular*}" in line:
            in_tabular = max(0, in_tabular - 1)

    return "\n".join(repaired_lines)


def _available_latex_engines() -> list[str]:
    engines = ["pdflatex", "xelatex", "lualatex"]
    return [engine for engine in engines if shutil.which(engine)]


def _run_latex_engine(
    engine: str,
    tex_path: Path,
    output_dir: Path,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-no-shell-escape",
        f"-output-directory={output_dir}",
        str(tex_path),
    ]
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=COMPILE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout=exc.stdout or "",
            stderr=f"Compilation timed out after {COMPILE_TIMEOUT_SECONDS}s.",
        )


def _read_log_output(output_dir: Path) -> str:
    log_path = output_dir / "resume.log"
    if not log_path.exists():
        return ""
    try:
        return log_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _categorize_compile_error(compiler_output: str, log_output: str) -> str:
    text = f"{compiler_output}\n{log_output}"
    if "timed out" in text.lower():
        return "timeout"
    if re.search(r"LaTeX Error:\s+File `[^`]+` not found\.", text):
        return "missing_package"
    if "Undefined control sequence" in text:
        return "undefined_control_sequence"
    if "macro parameter character #" in text or "Misplaced alignment tab character &" in text:
        return "unescaped_special_char"
    return "compile_error"


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
    latex_code: Annotated[str, "Complete valid LaTeX source for the resume document."] = ""
) -> str:
    """Compile LaTeX resume code into PDF, upload to Azure Blob, and return blob URL."""
    tool_name = "generate_resume_pdf"
    normalized_latex = _normalize_latex_input(latex_code)
    valid, validation_error = _validate_latex_input(normalized_latex)
    if not valid:
        error = f"validation: {validation_error}"
        return format_tool_failure(tool_name, error)

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            tex_path = tmp_path / "resume.tex"
            pdf_path = tmp_path / "resume.pdf"
            latex_source = normalized_latex
            engines = _available_latex_engines()
            if not engines:
                return format_tool_failure(
                    tool_name,
                    "compile: No LaTeX compiler available. Install pdflatex, xelatex, or lualatex.",
                )

            last_failure = "compile: Unknown LaTeX failure."
            attempted_escape_repair = False

            for compile_attempt in range(2):
                tex_path.write_text(latex_source, encoding="utf-8")

                for engine in engines:
                    compile_ok = True
                    combined_output = ""
                    completed = None
                    for _ in range(2):
                        completed = _run_latex_engine(engine, tex_path, tmp_path)
                        combined_output = "\n".join(
                            [combined_output, completed.stdout or "", completed.stderr or ""]
                        )
                        if completed.returncode != 0:
                            compile_ok = False
                            break

                    if compile_ok and pdf_path.exists():
                        break

                    log_output = _read_log_output(tmp_path)
                    category = _categorize_compile_error(combined_output, log_output)
                    concise_error = _extract_latex_error(combined_output, log_output)
                    last_failure = (
                        f"compile[{category}]: engine={engine}. "
                        f"{concise_error[:MAX_ERROR_CHARS]}"
                    )

                    if (
                        compile_attempt == 0
                        and not attempted_escape_repair
                        and category == "unescaped_special_char"
                    ):
                        repaired_latex = _repair_common_latex_text_issues(latex_source)
                        if repaired_latex != latex_source:
                            latex_source = repaired_latex
                            attempted_escape_repair = True
                            break
                else:
                    if not (compile_attempt == 0 and attempted_escape_repair):
                        break
                    continue

                if pdf_path.exists():
                    break

            if not pdf_path.exists():
                return format_tool_failure(tool_name, last_failure)

            pdf_bytes = pdf_path.read_bytes()
            if not pdf_bytes:
                error = "compile: Generated PDF is empty."
                return format_tool_failure(tool_name, error)

            blob_name = f"{uuid.uuid4()}.pdf"
            blob_url = _upload_pdf_to_blob(pdf_bytes, blob_name)
            if not blob_url:
                error = "upload: Blob upload completed but URL is empty."
                return format_tool_failure(
                    tool_name,
                    error,
                )

            return blob_url
    except Exception as exc:
        error = f"runtime: {exc}"
        return format_tool_failure(tool_name, error)
