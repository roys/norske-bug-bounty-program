#!/usr/bin/env python3
"""Validate programs.yaml and render the table into README.md between markers.

Usage: render.py [--validate | --check]
"""

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "programs.yaml"
README = ROOT / "README.md"
START = "<!-- programs:start -->"
END = "<!-- programs:end -->"

PLATFORMS = {
    "hackerone": ("HackerOne", "https://hackerone.com"),
    "intigriti": ("Intigriti", "https://intigriti.com"),
    "bugcrowd": ("Bugcrowd", "https://bugcrowd.com"),
    "yeswehack": ("YesWeHack", "https://yeswehack.com"),
    "synack": ("Synack", "https://synack.com"),
    "none": None,
}
VISIBILITY = ("public", "private-known", "undisclosed")
TYPES = ("bug-bounty", "rdp", "vdp")
REWARDS = {
    "money": ("💰", "Penger"),
    "hall-of-fame": ("🏆", "Hall of Fame"),
    "swag": ("👕", "Swag"),
}
MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "Mai", "Jun.", "Jul.", "Aug.", "Sep.", "Okt.", "Nov.", "Des."]
STATUS = {
    "active": None,
    "unknown": ("⚠️", "Usikker status"),
    "closed": ("🔴", "Stengt"),
}
SECTIONS = [
    ("💰 Offentlige bug bounty-program", None,
     lambda p: p["type"] == "bug-bounty" and p["visibility"] == "public"),
    ("🔒 Private bug bounty-program",
     "Private program krever invitasjon fra plattformen eller selskapet, men det er offentlig kjent at de finnes.",
     lambda p: p["type"] == "bug-bounty" and p["visibility"] == "private-known"),
    ("📨 Responsible disclosure / VDP", None,
     lambda p: p["type"] != "bug-bounty"),
]
LAUNCHED_RE = re.compile(r"^(<= )?\d{4}(-\d{2})?$")
TEXT_FIELDS = ("name", "unit", "source_name")
URL_FIELDS = ("url", "unit_url", "program_url", "source", "security_txt")
UNSAFE_TEXT_RE = re.compile(r"[|\[\]<>()`\\\n\r]")
URL_RE = re.compile(r"^https://[^\s|<>()\[\]`\\]+$")


def fail(index, msg):
    sys.exit(f"programs.yaml entry {index + 1}: {msg}")


def validate(programs):
    if not isinstance(programs, list):
        sys.exit("programs.yaml must be a list")
    for i, p in enumerate(programs):
        if not isinstance(p, dict):
            fail(i, "must be a mapping")
        for key in ("platform", "visibility", "type", "rewards"):
            if key not in p:
                fail(i, f"missing '{key}'")
        for key in TEXT_FIELDS:
            if key in p and (not isinstance(p[key], str) or not p[key].strip() or UNSAFE_TEXT_RE.search(p[key])):
                fail(i, f"'{key}' must be plain text without |[]<>()` characters")
        for key in URL_FIELDS:
            if key in p and (not isinstance(p[key], str) or not URL_RE.match(p[key])):
                fail(i, f"'{key}' must be a plain https:// URL")
        if not isinstance(p["rewards"], list):
            fail(i, "'rewards' must be a list (may be empty)")
        if p["platform"] not in PLATFORMS:
            fail(i, f"unknown platform '{p['platform']}'")
        if p["visibility"] not in VISIBILITY:
            fail(i, f"unknown visibility '{p['visibility']}'")
        if p["type"] not in TYPES:
            fail(i, f"unknown type '{p['type']}'")
        for r in p["rewards"]:
            if r not in REWARDS:
                fail(i, f"unknown reward '{r}'")
        if p["visibility"] == "undisclosed":
            if "name" in p:
                fail(i, "undisclosed programs must not have a name")
        elif "name" not in p or "url" not in p:
            fail(i, "missing 'name' or 'url'")
        if "launched" in p and not LAUNCHED_RE.match(str(p["launched"])):
            fail(i, f"bad 'launched' value '{p['launched']}' (use YYYY, YYYY-MM or '<= YYYY')")
        if p.get("status", "active") not in STATUS:
            fail(i, f"unknown status '{p['status']}'")


def link(text, url):
    return f"[{text}]({url})" if url else text


def company(p):
    out = link(p["name"], p["url"])
    if "unit" in p:
        out += " - " + link(p["unit"], p.get("unit_url"))
    state = p.get("status", "active")
    if state == "closed":
        out = f"~~{out}~~"
    if state != "active":
        emoji, title = STATUS[state]
        out += f' <span title="{title}">{emoji}</span>'
    return out


def platform_program(p):
    """Platform name (or 'Eget program' when self-hosted), linked to the program page when known."""
    meta = PLATFORMS[p["platform"]]
    url = p.get("program_url")
    text = meta[0] if meta else "Eget program"
    return link(text, url) if url else text


def rewards(p):
    if not p["rewards"]:
        return "-"
    return " ".join(f'<span title="{title}">{emoji}</span>' for emoji, title in (REWARDS[r] for r in p["rewards"]))


def month_year(value):
    prefix = ""
    if value.startswith("<= "):
        prefix, value = "<= ", value[3:]
    if "-" in value:
        year, month = value.split("-")
        return f"{prefix}{MONTHS[int(month) - 1]} {year}"
    return prefix + value


def launched(p):
    value = str(p.get("launched", "")).strip()
    return month_year(value) if value else "?"


def security_txt(p):
    url = p.get("security_txt")
    return link("security.txt", url) if url else "-"


def source(p):
    if "source" not in p:
        return "-"
    return link(p.get("source_name", "Kilde"), p["source"])


def sort_key(p):
    return (p["visibility"] == "undisclosed", p.get("name", "").lower(), p.get("unit", ""), p["type"])


COLUMNS = [
    ("Firma", company),
    ("Plattform / program", platform_program),
    ("Dusør", rewards),
    ("security.txt", security_txt),
    ("Lansert", launched),
    ("Kilde", source),
]


def render_table(programs, with_source):
    columns = [c for c in COLUMNS if with_source or c[0] != "Kilde"]
    lines = [
        "|" + "|".join(name for name, _ in columns) + "|",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for p in sorted(programs, key=sort_key):
        lines.append("|" + "|".join(cell(p) for _, cell in columns) + "|")
    return "\n".join(lines)


def last_updated():
    """Date of the last commit touching the data file, or None outside git."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", DATA.name],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def undisclosed_note(programs):
    n = len(programs)
    noun = "norsk privat program" if n == 1 else "norske private programmer"
    return f"**I tillegg kjenner man til minst {n} {noun} hvor selskapet ikke kan oppgis.**"


def render(programs):
    active = [p for p in programs if p.get("status", "active") != "closed"]
    public_money = [p for p in active if SECTIONS[0][2](p) and "money" in p["rewards"]]
    undisclosed = [p for p in active if p["visibility"] == "undisclosed"]
    stats = f"**{len(active)} aktive program · {len(public_money)} offentlige bug bounty-program med pengedusør"
    updated = last_updated()
    if updated:
        stats += f" · sist oppdatert {updated}"
    stats += "**"
    parts = [stats]
    for title, intro, match in SECTIONS:
        rows = [p for p in programs if match(p)]
        if rows:
            table = render_table(rows, with_source=match is SECTIONS[1][2])
            parts.append(f"### {title}\n\n" + (f"{intro}\n\n" if intro else "") + table)
        if match is SECTIONS[1][2] and undisclosed:
            parts.append(undisclosed_note(undisclosed))
    parts.append("Dusør: 💰 penger · 🏆 hall of fame · 👕 swag. ⚠️ = usikker status · 🔴 = stengt.")
    return "\n\n".join(parts)


def main():
    programs = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    validate(programs)
    if "--validate" in sys.argv:
        print(f"programs.yaml is valid ({len(programs)} programs)")
        return
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        sys.exit(f"README.md is missing {START} / {END} markers")
    before, rest = readme.split(START, 1)
    _, after = rest.split(END, 1)
    updated = f"{before}{START}\n{render(programs)}\n{END}{after}"
    if "--check" in sys.argv:
        if updated != readme:
            sys.exit("README.md is out of date; run scripts/render.py")
        print("README.md is up to date")
        return
    README.write_text(updated, encoding="utf-8")
    print(f"Rendered {len(programs)} programs into README.md")


if __name__ == "__main__":
    main()
