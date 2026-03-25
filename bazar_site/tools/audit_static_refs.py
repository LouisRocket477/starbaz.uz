import re
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    templates_root = root / "templates"
    static_root = root / "static"

    if not templates_root.exists():
        print(f"templates folder not found: {templates_root}")
        return 2
    if not static_root.exists():
        print(f"static folder not found: {static_root}")
        return 2

    # We intentionally keep this regex simple and robust.
    # It matches: {% static 'path/to/file.ext' %}
    pattern = re.compile(r"""{%\s*static\s*'([^']+)'\s*%}""")

    seen: set[str] = set()
    missing: list[tuple[str, str]] = []

    for tpl in templates_root.rglob("*.html"):
        txt = tpl.read_text(encoding="utf-8", errors="ignore")
        for m in pattern.finditer(txt):
            rel = m.group(1).strip()
            if not rel or rel in seen:
                continue
            seen.add(rel)
            if not (static_root / rel).exists():
                missing.append((rel, str(tpl.relative_to(root))))

    print(f"static refs found: {len(seen)}")
    print(f"missing static files: {len(missing)}")
    for rel, where in missing[:200]:
        print(f"MISSING: {rel}  (referenced in {where})")

    return 0 if not missing else 1


if __name__ == '__main__':
    raise SystemExit(main())

