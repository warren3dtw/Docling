from __future__ import annotations

import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from .config import AppConfig, load_config
from .pipeline import build_directory, build_pdf
from .quality import validate_output
from .state import load_json

app = typer.Typer(help="本機優先、可恢復的 PDF → Markdown 知識庫工具。", no_args_is_help=True)


def _memory_gib() -> float | None:
    try:
        if sys.platform == "win32":
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong), ("available", ctypes.c_ulonglong), ("total_page", ctypes.c_ulonglong), ("available_page", ctypes.c_ulonglong), ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong), ("extended", ctypes.c_ulonglong)]

            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return round(status.total / 1024**3, 2)
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3, 2)
    except (AttributeError, OSError, ValueError):
        return None


def _cfg(path: Path) -> AppConfig:
    config = load_config(path)
    for field in ("input_dir", "work_dir", "output_dir"):
        value = getattr(config, field)
        if not value.is_absolute():
            setattr(config, field, (Path.cwd() / value).resolve())
    return config


@app.command()
def doctor() -> None:
    """檢查 Python、GPU、Docling、憑證與路徑，不呼叫模型。"""
    load_dotenv()
    gpu = "未偵測"
    if shutil.which("nvidia-smi"):
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"], capture_output=True, text=True, check=False)
        gpu = result.stdout.strip() or f"查詢失敗：{result.stderr.strip()}"
    payload = {
        "os": platform.platform(), "python": sys.version.split()[0], "executable": sys.executable,
        "cpu_count": os.cpu_count(), "ram_gib": _memory_gib(), "gpu": gpu, "docling_installed": importlib.util.find_spec("docling") is not None,
        "vision_model": os.getenv("VISION_MODEL") or "未設定", "summary_model": os.getenv("SUMMARY_MODEL") or "未設定",
        "api_key_present": bool(os.getenv("OPENAI_COMPATIBLE_API_KEY")),
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command()
def build(
    input: Annotated[Path, typer.Option("--input", help="PDF 輸入目錄")] = Path("data/input"),
    config: Annotated[Path, typer.Option("--config")] = Path("config/default.yaml"),
    skip_vlm: Annotated[bool, typer.Option("--skip-vlm")] = False,
    skip_llm: Annotated[bool, typer.Option("--skip-llm")] = False,
    force: Annotated[bool, typer.Option("--force")] = False,
) -> None:
    """分批處理輸入目錄中的全部 PDF。"""
    cfg = _cfg(config)
    try:
        results = build_directory(input.resolve(), cfg, force, skip_vlm, skip_llm)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        typer.echo(f"錯誤：{exc}", err=True)
        raise typer.Exit(1)
    for manifest, report in results:
        typer.echo(f"{manifest['document_id']}: {manifest['status']}，解析 {report['pages_parsed']}/{report['pages_total']} 頁，QA={'通過' if report['valid'] else '需檢查'}")


def _find_document(document: str, cfg: AppConfig) -> tuple[Path, dict]:
    manifest_path = cfg.work_dir / document / "manifest.json"
    manifest = load_json(manifest_path)
    if not manifest:
        raise FileNotFoundError(f"找不到文件狀態：{document}")
    return manifest_path, manifest


@app.command()
def resume(document: str, config: Path = Path("config/default.yaml")) -> None:
    """只重試失敗或不完整的批次。"""
    cfg = _cfg(config)
    try:
        _, manifest = _find_document(document, cfg)
        _, report = build_pdf(Path(manifest["source_path"]), cfg)
        typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
    except (FileNotFoundError, RuntimeError) as exc:
        typer.echo(f"錯誤：{exc}", err=True)
        raise typer.Exit(1)


@app.command("validate")
def validate_command(document: str, config: Path = Path("config/default.yaml")) -> None:
    """驗證 Markdown、連結、JSONL 與批次完整性。"""
    cfg = _cfg(config)
    try:
        _, manifest = _find_document(document, cfg)
        report = validate_output(cfg.output_dir / document, manifest)
        typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
        if not report["valid"]:
            raise typer.Exit(2)
    except FileNotFoundError as exc:
        typer.echo(f"錯誤：{exc}", err=True)
        raise typer.Exit(1)


@app.command("index")
def index_command(document: str, config: Path = Path("config/default.yaml")) -> None:
    """從已保存的解析結果重建輸出與索引。"""
    cfg = _cfg(config)
    try:
        _, manifest = _find_document(document, cfg)
        build_pdf(Path(manifest["source_path"]), cfg)
        typer.echo(f"已重建 {document} 的索引。")
    except (FileNotFoundError, RuntimeError) as exc:
        typer.echo(f"錯誤：{exc}", err=True)
        raise typer.Exit(1)


@app.command()
def enrich(document: str, config: Path = Path("config/default.yaml")) -> None:
    """模型配置後的增強入口；目前驗證配置並保留解析快取。"""
    cfg = _cfg(config)
    _, manifest = _find_document(document, cfg)
    if not cfg.vision.enabled and not cfg.summary.enabled:
        typer.echo("錯誤：vision 與 summary 均未啟用；未對內容做任何變更。", err=True)
        raise typer.Exit(1)
    # build_pdf validates and reuses successful parsing artifacts before provider calls.
    build_pdf(Path(manifest["source_path"]), cfg)
    typer.echo(f"已完成 {document} 的已配置增強步驟。")


if __name__ == "__main__":
    app()
