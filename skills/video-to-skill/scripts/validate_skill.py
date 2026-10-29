#!/usr/bin/env python3
"""
validate_skill.py — structural sanity check for a Claude Code skill authored by video-to-skill.

Not a substitute for the rehearsal (running the skill in a fresh subagent), but catches the
mechanical mistakes that stop a skill from loading or firing.

Usage:  python3 validate_skill.py <path-to-skill-dir-or-SKILL.md>
Exit 0 = all checks pass; exit 1 = one or more failures.
"""
import os
import re
import sys

MAX_NAME = 64
MAX_DESC = 1024  # SKILL.md descriptions should be a few sentences, not an essay


def find_skill_md(target):
    if os.path.isfile(target):
        return target
    cand = os.path.join(target, "SKILL.md")
    return cand if os.path.isfile(cand) else None


def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None, "no YAML frontmatter (must start with a --- ... --- block)"
    fm = {}
    key, buf = None, []
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if mm and not line.startswith(" "):
            if key:
                fm[key] = "\n".join(buf).strip()
            key, buf = mm.group(1), [mm.group(2)]
        else:
            buf.append(line)
    if key:
        fm[key] = "\n".join(buf).strip()
    return fm, None


def check(target):
    problems, warnings = [], []
    skill_md = find_skill_md(target)
    if not skill_md:
        return [f"no SKILL.md found at {target}"], []
    skill_dir = os.path.dirname(os.path.abspath(skill_md))
    text = open(skill_md, encoding="utf-8").read()

    fm, err = parse_frontmatter(text)
    if err:
        problems.append(err)
        return problems, warnings

    name = fm.get("name", "")
    desc = fm.get("description", "")
    if not name:
        problems.append("frontmatter: missing `name`")
    elif not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
        problems.append(f"frontmatter: `name` must be kebab-case (got '{name}')")
    elif len(name) > MAX_NAME:
        problems.append(f"frontmatter: `name` too long ({len(name)} > {MAX_NAME})")
    if os.path.basename(skill_dir) != name and name:
        warnings.append(f"skill dir '{os.path.basename(skill_dir)}' != name '{name}' (should match)")

    if not desc:
        problems.append("frontmatter: missing `description` (skill will never trigger well)")
    else:
        if len(desc) > MAX_DESC:
            warnings.append(f"description is long ({len(desc)} chars) — keep it tight")
        if not re.search(r"[Uu]se (this|when)|when the user|for (ing|when)", desc) and \
           "when" not in desc.lower():
            warnings.append("description has no 'use when …' trigger cues — may not fire reliably")

    body = text[text.find("---", 3) + 3:].strip()
    if len(body) < 80:
        problems.append("SKILL.md body is essentially empty — no instructions")

    # any referenced local files exist?
    for ref in re.findall(r"`(scripts/[^`]+|references/[^`]+)`", body):
        ref = ref.split()[0]
        if not os.path.exists(os.path.join(skill_dir, ref)):
            warnings.append(f"references '{ref}' but that file is missing")

    # bundled python scripts should at least parse (compile in-memory — do NOT write __pycache__
    # into the skill dir, which would pollute it and break rsync parity)
    scripts_dir = os.path.join(skill_dir, "scripts")
    if os.path.isdir(scripts_dir):
        for fn in sorted(os.listdir(scripts_dir)):
            if fn.endswith(".py"):
                p = os.path.join(scripts_dir, fn)
                try:
                    compile(open(p, encoding="utf-8").read(), p, "exec")
                except SyntaxError as e:
                    problems.append(f"scripts/{fn} does not compile: {e}")
    return problems, warnings


def main():
    if len(sys.argv) != 2:
        print("usage: validate_skill.py <skill-dir-or-SKILL.md>", file=sys.stderr)
        sys.exit(2)
    problems, warnings = check(sys.argv[1])
    for w in warnings:
        print(f"  ⚠ {w}")
    if problems:
        for p in problems:
            print(f"  ✗ {p}")
        print(f"\nFAIL — {len(problems)} problem(s), {len(warnings)} warning(s)")
        sys.exit(1)
    print(f"\nOK — structural checks pass ({len(warnings)} warning(s)).")
    print("Now rehearse it: run the skill in a fresh subagent on a real task (see validation-checklist.md).")
    sys.exit(0)


if __name__ == "__main__":
    main()
