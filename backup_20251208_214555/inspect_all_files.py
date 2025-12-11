import os
import json
from pathlib import Path

# جذر المشروع = المجلد الذي فيه هذا الملف
ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)
INDEX_PATH = ARTIFACTS_DIR / "all_files_index.json"
SUMMARY_PATH = ARTIFACTS_DIR / "all_files_summary.json"

# خريطة بسيطة من الامتداد → نوع/لغة
EXT_KIND_MAP = {
    # Python / Backend
    ".py": "code/python",
    # JS / TS / Frontend
    ".js": "code/javascript",
    ".jsx": "code/javascript",
    ".ts": "code/typescript",
    ".tsx": "code/typescript",
    # Web
    ".html": "markup/html",
    ".htm": "markup/html",
    ".css": "style/css",
    ".scss": "style/scss",
    ".sass": "style/sass",
    # Data / Config
    ".json": "data/json",
    ".yml": "data/yaml",
    ".yaml": "data/yaml",
    ".toml": "data/toml",
    ".ini": "data/ini",
    ".cfg": "data/ini",
    ".env": "config/env",
    # Docs
    ".md": "docs/markdown",
    ".rst": "docs/restructuredtext",
    ".txt": "docs/text",
    ".pdf": "docs/pdf",
    ".docx": "docs/word",
    # Notebooks
    ".ipynb": "notebook/jupyter",
    # Shell / Scripts
    ".sh": "script/shell",
    ".ps1": "script/powershell",
    ".bat": "script/batch",
    ".cmd": "script/batch",
    ".psm1": "script/powershell",
    # Images
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg",
    ".ico": "image/ico",
    ".webp": "image/webp",
    # Archives / binaries (للتصنيف فقط)
    ".zip": "archive/zip",
    ".tar": "archive/tar",
    ".gz": "archive/gzip",
    ".rar": "archive/rar",
    ".7z": "archive/7z",
    ".exe": "binary/exe",
    ".dll": "binary/dll",
    ".pyd": "binary/pyd",
    ".so": "binary/so",
}

# امتدادات نتعامل معها كنص (نقدر نفتحها ونقرأها)
TEXT_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".htm", ".css", ".scss", ".sass",
    ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".env",
    ".md", ".rst", ".txt", ".sh", ".ps1", ".bat", ".cmd", ".psm1",
}


def guess_kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in EXT_KIND_MAP:
        return EXT_KIND_MAP[ext]
    # fallback على حسب الامتداد نفسه
    if ext:
        return f"unknown/{ext.lstrip('.') }"
    return "unknown/no_extension"


def is_text_file(path: Path, max_bytes: int = 1024) -> bool:
    """ محاولة بسيطة للتفريق بين النصّي و الثنائي:
    - لو الامتداد معروف كنص → True
    - وإلا نقرأ أول 1KB ونشوف هل فيه بايتات غير قابلة للطباعة.
    """
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return True
    try:
        with path.open("rb") as f:
            chunk = f.read(max_bytes)
            if b"\0" in chunk:
                return False
            # لو معظم البايتات ضمن نطاق ASCII/UTF-8 نعتبره نص
            text_like = sum(32 <= b <= 126 or b in (9, 10, 13) for b in chunk)
            return text_like / max(len(chunk), 1) > 0.8
    except Exception:
        return False


def scan_project(root: Path):
    """ يمشي على كل الملفات داخل المشروع، ويجمع:
    - المسار النسبي
    - الحجم بالبايت
    - النوع/اللغة (kind)
    - هل هو نصّي أم لا
    - إحصائيات محتوى بسيطة للملفات النصية (عدد الأسطر، عدد TODO/FIXME)
    """
    all_files = []
    summary_by_kind = {}
    summary_by_ext = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirpath = Path(dirpath)
        # تجاهل مجلدات معيّنة (اختياري)
        rel_dir = dirpath.relative_to(root)
        if any(part in {".git", ".venv", "__pycache__", ".idea", ".vscode"} for part in rel_dir.parts):
            continue
        for name in filenames:
            full_path = dirpath / name
            try:
                rel_path = full_path.relative_to(root)
            except Exception:
                rel_path = full_path
            # تجاهل بعض الملفات الخاصة بالأدوات إن أحببت
            # (هنا نحتفظ بمجلد artifacts كي نحتفظ بنظرة شاملة)
            try:
                size = full_path.stat().st_size
            except Exception:
                size = 0
            ext = full_path.suffix.lower()
            kind = guess_kind(full_path)
            is_text = is_text_file(full_path)

            file_info = {
                "path": str(rel_path).replace("\\", "/"),
                "size_bytes": size,
                "ext": ext or "",
                "kind": kind,
                "is_text": is_text,
            }

            # لو الملف نصّي: جمع إحصائيات محتوى بسيطة
            if is_text and size <= 5 * 1024 * 1024:  # حد 5MB احتياطًا
                try:
                    text = full_path.read_text(encoding="utf-8", errors="replace")
                    lines = text.splitlines()
                    file_info["line_count"] = len(lines)
                    file_info["todo_count"] = sum("TODO" in line or "todo" in line for line in lines)
                    file_info["fixme_count"] = sum("FIXME" in line or "fixme" in line for line in lines)
                except Exception as e:
                    file_info["read_error"] = str(e)

            all_files.append(file_info)

            # تحديث summary_by_kind
            k = kind
            s_k = summary_by_kind.setdefault(k, {"files": 0, "total_bytes": 0})
            s_k["files"] += 1
            s_k["total_bytes"] += size

            # تحديث summary_by_ext
            e = ext or "<no_ext>"
            s_e = summary_by_ext.setdefault(e, {"files": 0, "total_bytes": 0, "kind": kind})
            s_e["files"] += 1
            s_e["total_bytes"] += size

    # حفظ الـ index الكامل
    try:
        INDEX_PATH.write_text(
            json.dumps(
                {
                    "root": str(root),
                    "total_files": len(all_files),
                    "files": all_files,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception as e:
        print("Failed to write index:", e)

    # حفظ ملخص الأنواع والامتدادات
    try:
        SUMMARY_PATH.write_text(
            json.dumps(
                {
                    "root": str(root),
                    "summary_by_kind": summary_by_kind,
                    "summary_by_ext": summary_by_ext,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception as e:
        print("Failed to write summary:", e)

    # طباعة ملخص سريع على الشاشة
    print("=== Scan complete ===")
    print(f"Root: {root}")
    print(f"Total files: {len(all_files)}")
    print("\n== By kind (top) ==")
    for kind, info in sorted(summary_by_kind.items(), key=lambda kv: kv[1]["files"], reverse=True):
        print(f"- {kind:20s} files={info['files']:5d} size={info['total_bytes']/1024:.1f} KB")

    print("\n== By extension (top 30) ==")
    by_ext_sorted = sorted(summary_by_ext.items(), key=lambda kv: kv[1]["files"], reverse=True)[:30]
    for ext, info in by_ext_sorted:
        print(f"- {ext:8s} files={info['files']:5d} size={info['total_bytes']/1024:.1f} KB kind={info['kind']}")


if __name__ == "__main__":
    scan_project(ROOT)
