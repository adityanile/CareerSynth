import subprocess
from pathlib import Path


def _minimal_latex() -> str:
    return r"""
\documentclass{article}
\begin{document}
\textbf{Alex Doe}
Hello world.
\end{document}
""".strip()


def test_generate_resume_pdf_persists_resume_record(app_module, monkeypatch):
    from agents.tools import resume_pdf_tool

    captured: dict[str, str] = {}

    def _fake_run_latex_engine(engine: str, tex_path: Path, output_dir: Path):
        (output_dir / "resume.pdf").write_bytes(b"%PDF-1.4 fake")
        return subprocess.CompletedProcess(args=[engine, str(tex_path)], returncode=0, stdout="", stderr="")

    def _fake_create_resume_for_user(
        oid: str,
        resume_name: str,
        resume_description: str,
        resume: str,
    ):
        captured["oid"] = oid
        captured["resume_name"] = resume_name
        captured["resume_description"] = resume_description
        captured["resume"] = resume
        return {"id": 1}

    monkeypatch.setattr(resume_pdf_tool, "_available_latex_engines", lambda: ["pdflatex"])
    monkeypatch.setattr(resume_pdf_tool, "_run_latex_engine", _fake_run_latex_engine)
    monkeypatch.setattr(resume_pdf_tool, "_upload_pdf_to_blob", lambda _bytes, _name: "https://blob/resume.pdf")
    monkeypatch.setattr(resume_pdf_tool, "require_current_oid", lambda: "user-1")
    monkeypatch.setattr(resume_pdf_tool, "create_resume_for_user", _fake_create_resume_for_user)

    result = resume_pdf_tool.generate_resume_pdf(
        latex_code=_minimal_latex(),
        resume_name="SWE Resume",
        resume_description="Generated from tool",
    )

    assert result == "https://blob/resume.pdf"
    assert captured == {
        "oid": "user-1",
        "resume_name": "SWE Resume",
        "resume_description": "Generated from tool",
        "resume": "https://blob/resume.pdf",
    }


def test_generate_resume_pdf_uses_default_tracking_fields(app_module, monkeypatch):
    from agents.tools import resume_pdf_tool

    captured: dict[str, str] = {}

    def _fake_run_latex_engine(engine: str, tex_path: Path, output_dir: Path):
        (output_dir / "resume.pdf").write_bytes(b"%PDF-1.4 fake")
        return subprocess.CompletedProcess(args=[engine, str(tex_path)], returncode=0, stdout="", stderr="")

    def _fake_create_resume_for_user(
        oid: str,
        resume_name: str,
        resume_description: str,
        resume: str,
    ):
        captured["oid"] = oid
        captured["resume_name"] = resume_name
        captured["resume_description"] = resume_description
        captured["resume"] = resume
        return {"id": 1}

    monkeypatch.setattr(resume_pdf_tool, "_available_latex_engines", lambda: ["pdflatex"])
    monkeypatch.setattr(resume_pdf_tool, "_run_latex_engine", _fake_run_latex_engine)
    monkeypatch.setattr(resume_pdf_tool, "_upload_pdf_to_blob", lambda _bytes, _name: "https://blob/resume.pdf")
    monkeypatch.setattr(resume_pdf_tool, "require_current_oid", lambda: "user-1")
    monkeypatch.setattr(resume_pdf_tool, "create_resume_for_user", _fake_create_resume_for_user)

    result = resume_pdf_tool.generate_resume_pdf(latex_code=_minimal_latex())

    assert result == "https://blob/resume.pdf"
    assert captured["oid"] == "user-1"
    assert captured["resume_name"] == "Alex Doe Resume"
    assert captured["resume_description"] == "Auto-saved after successful PDF generation."
    assert captured["resume"] == "https://blob/resume.pdf"
