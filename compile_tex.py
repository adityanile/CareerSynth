#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _upload_pdf_to_azure(pdf_bytes: bytes, blob_name: str) -> str:
    try:
        from azure.storage.blob import BlobServiceClient, ContentSettings
    except ImportError as exc:
        raise RuntimeError(
            "azure-storage-blob is not installed. Install it with: pip install azure-storage-blob"
        ) from exc

    account_name = _required_env("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = _required_env("AZURE_STORAGE_ACCOUNT_KEY")
    container_name = _required_env("AZURE_STORAGE_CONTAINER_NAME")

    account_url = f"https://{account_name}.blob.core.windows.net"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=account_key)
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_name,
    )
    blob_client.upload_blob(
        pdf_bytes,
        overwrite=True,
        content_settings=ContentSettings(
            content_type="application/pdf",
            content_disposition="inline",
        ),
    )
    return blob_client.url


def compile_tex(tex_file: Path) -> int:
    if not tex_file.exists():
        print(f"Error: file not found: {tex_file}", file=sys.stderr)
        return 1

    if tex_file.suffix.lower() != ".tex":
        print(f"Error: expected a .tex file, got: {tex_file.name}", file=sys.stderr)
        return 1

    output_dir = tex_file.parent
    pdf_path = tex_file.with_suffix(".pdf")
    log_path = tex_file.with_suffix(".log")

    completed_process = subprocess.run(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={output_dir}",
            str(tex_file),
        ],
        capture_output=True,
        text=True,
    )

    print(f"Return code: {completed_process.returncode}")
    if completed_process.returncode == 0:
        print("LaTeX compilation succeeded.")
        if not pdf_path.exists():
            print("Error: compiled PDF not found.", file=sys.stderr)
            return 1
        pdf = pdf_path.read_bytes()

        try:
            blob_name = f"{uuid.uuid4()}.pdf"
            blob_url = _upload_pdf_to_azure(pdf, blob_name)
            print(f"Uploaded PDF to Azure Blob Storage successfully as: {blob_name}")
            print(f"Blob URL: {blob_url}")
            if pdf_path.exists():
                pdf_path.unlink()
                print(f"Removed local PDF: {pdf_path}")
        except Exception as exc:
            print(f"Error uploading PDF to Azure Blob Storage: {exc}", file=sys.stderr)
            return 1
    else:
        print("LaTeX compilation failed.", file=sys.stderr)
        if completed_process.stderr:
            print(completed_process.stderr, file=sys.stderr)
        elif completed_process.stdout:
            print(completed_process.stdout, file=sys.stderr)

    if completed_process.returncode == 0:
        print(f"PDF bytes length: {len(pdf)}")
    if log_path.exists():
        print(f"Log size: {log_path.stat().st_size} bytes")

    return completed_process.returncode


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description=(
            "Compile a .tex file using pdflatex and upload the generated PDF "
            "to Azure Blob Storage."
        )
    )
    parser.add_argument("tex_file", help="Path to the .tex file")
    args = parser.parse_args()
    return compile_tex(Path(args.tex_file))


if __name__ == "__main__":
    raise SystemExit(main())
