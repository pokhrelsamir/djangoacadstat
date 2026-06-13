#!/usr/bin/env python3
"""Migrate dashboard templates to the AcadStat design system partials."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "core" / "templates" / "core"

SKIP_DIRS = {"emails", "admin"}
SKIP_FILES = {
    "base_app.html",
    "design_head.html",
    "app_navbar.html",
    "theme_script.html",
    "mark_sheet_pdf.html",
    "seating_plan_hall_ticket.html",
    "seating_plan_bulk_hall_tickets.html",
}

THEME_INIT = """<script>
(function() {
    document.documentElement.setAttribute('data-theme', localStorage.getItem('theme') || 'dark');
})();
</script>"""

THEME_TOGGLE_BTN = """
            <button class="theme-toggle ds-toggle" id="themeToggle" type="button" aria-label="Toggle theme">
                <svg class="sun-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/></svg>
                <svg class="moon-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            </button>"""

THEME_SCRIPT_INCLUDE = "{% include 'core/partials/theme_script.html' %}\n"

OLD_THEME_BLOCK = re.compile(
    r"\s*<!-- Theme Toggle Script -->\s*<script>.*?</script>\s*",
    re.DOTALL | re.IGNORECASE,
)

OLD_THEME_INIT = re.compile(
    r"\s*<!-- Theme detection script[^>]*-->\s*<script>\s*\(function\s*\(\)\s*\{.*?\}\)\(\);\s*</script>\s*",
    re.DOTALL | re.IGNORECASE,
)

HEAD_START = re.compile(
    r"<head>\s*<meta charset=\"UTF-8\">\s*"
    r"(?:<meta name=\"viewport\"[^>]*>\s*)?"
    r"<title>(?P<title>[^<]+)</title>\s*"
    r"\{% load static %\}\s*"
    r"<link rel=\"stylesheet\" href=\"\{% static 'css/style.css' %\}\">\s*",
    re.DOTALL,
)

HTML_TAG = re.compile(r'<html lang="en"(?:\s+data-theme="[^"]*")?>')


def should_skip(path: Path) -> bool:
    if path.name in SKIP_FILES:
        return True
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if path.suffix != ".html":
        return True
    return False


def migrate_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "design_head.html" in text or "extends 'core/partials/base_app.html'" in text:
        return False
    if "<!DOCTYPE html>" not in text:
        return False

    original = text

    text = HTML_TAG.sub('<html lang="en">', text)

    m = HEAD_START.search(text)
    if m:
        title = m.group("title").strip()
        replacement = (
            "<head>\n"
            f"    {{% include 'core/partials/design_head.html' with page_title=\"{title}\" %}}\n"
        )
        text = text[: m.start()] + replacement + text[m.end() :]
        text = OLD_THEME_INIT.sub("\n", text)

    if re.search(r"<body(?:\s+class=\"[^\"]*\")?>", text):
        text = re.sub(
            r"<body(?:\s+class=\"([^\"]*)\")?>",
            lambda m: f'<body class="app-page {m.group(1) or ""}'.strip() + '">',
            text,
            count=1,
        )

    if 'id="themeToggle"' not in text and '<nav class="navbar">' in text:
        text = text.replace(
            "</div>\n    </nav>",
            THEME_TOGGLE_BTN + "\n        </div>\n    </nav>",
            1,
        )
        if 'class="navbar app-nav-style"' not in text:
            text = text.replace(
                '<nav class="navbar">',
                '<nav class="navbar app-nav-style">',
                1,
            )

    text = OLD_THEME_BLOCK.sub("\n", text)

    if "theme_script.html" not in text and "</body>" in text:
        text = text.replace("</body>", f"\n    {THEME_SCRIPT_INCLUDE}</body>", 1)

    if "landingTheme" in text:
        text = text.replace("localStorage.getItem('landingTheme')", "localStorage.getItem('theme')")
        text = text.replace("localStorage.setItem('landingTheme'", "localStorage.setItem('theme'")

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = []
    for path in sorted(TEMPLATES.rglob("*.html")):
        if should_skip(path):
            continue
        if migrate_file(path):
            changed.append(path.relative_to(ROOT))
    print(f"Migrated {len(changed)} templates:")
    for p in changed:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
