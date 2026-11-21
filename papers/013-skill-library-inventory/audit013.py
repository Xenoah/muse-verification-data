#!/usr/bin/env python3
"""Paper 013: full-population structural inventory of Muse's skill library.
Read-only. Per-skill: SKILL.md bytes/lines, total files/bytes in skill dir,
extension breakdown, subdir presence, frontmatter name/description presence.
Email-pattern scan is COUNT ONLY (strings never output).
Population: top-level dirs of /opt/muse/skills (system) and
~/workspace/custom-skills (custom). A nested template SKILL.md inside
custom-connector-setup/templates is counted as an accompanying file, not a skill.
"""
import os, re, json, statistics
from pathlib import Path
from collections import Counter

HOME = Path.home()
ROOTS = {"system": Path("/opt/muse/skills"), "custom": HOME / "workspace/custom-skills"}
EMAIL_RE = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def lines_of(p: Path):
    try:
        data = p.read_bytes()
    except Exception:
        return 0, 0, 1
    return len(data), data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0), 0

def frontmatter_flags(p: Path):
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False, False
    if not text.startswith("---"):
        return False, False
    end = text.find("\n---", 3)
    fm = text[3:end] if end != -1 else text[:2000]
    return ("name:" in fm), ("description:" in fm)

def main():
    skills = []
    errors = 0
    ext_counter = Counter()
    total_files_all = 0
    for kind, root in ROOTS.items():
        for d in sorted([x for x in root.iterdir() if x.is_dir()], key=lambda x: x.name):
            skill_md = d / "SKILL.md"
            if not skill_md.exists():
                skills.append({"kind": kind, "name": d.name, "has_skill_md": False})
                continue
            sb, sl, e = lines_of(skill_md); errors += e
            has_name, has_desc = frontmatter_flags(skill_md)
            try:
                first_line = skill_md.read_text(encoding="utf-8", errors="replace").splitlines()[0] if sb else ""
            except Exception:
                first_line = ""
            has_h1 = first_line.startswith("# ")
            has_yaml = (d / "skill.yaml").exists()
            nfiles = 0; tbytes = 0; subdirs = set(); nested_skill_md = 0
            for dirpath, dirnames, filenames in os.walk(d):
                for fn in filenames:
                    fp = Path(dirpath) / fn
                    rel = fp.relative_to(d)
                    if len(rel.parts) > 1:
                        subdirs.add(rel.parts[0])
                    if fp != skill_md and fn == "SKILL.md":
                        nested_skill_md += 1
                    try:
                        sz = fp.stat().st_size
                    except Exception:
                        errors += 1; continue
                    nfiles += 1; tbytes += sz
                    ext_counter[fp.suffix.lower() or "(none)"] += 1
            skills.append({
                "kind": kind, "name": d.name, "has_skill_md": True,
                "skill_md_bytes": sb, "skill_md_lines": sl,
                "total_files": nfiles, "total_bytes": tbytes,
                "extra_files": nfiles - 1, "subdirs": sorted(subdirs),
                "nested_skill_md": nested_skill_md,
                "fm_name": has_name, "fm_description": has_desc,
                "has_h1": has_h1, "has_skill_yaml": has_yaml,
            })
            total_files_all += nfiles
    valid = [s for s in skills if s.get("has_skill_md")]
    # email pattern count only, across all files under both roots
    email_count = 0; email_files = 0
    for root in ROOTS.values():
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                fp = Path(dirpath) / fn
                try:
                    data = fp.read_bytes()
                except Exception:
                    continue
                m = EMAIL_RE.findall(data)
                if m:
                    email_count += len(m); email_files += 1
    def agg(group):
        return {
            "skills": len(group),
            "skill_md_bytes": sum(s["skill_md_bytes"] for s in group),
            "skill_md_lines": sum(s["skill_md_lines"] for s in group),
            "total_files": sum(s["total_files"] for s in group),
            "total_bytes": sum(s["total_bytes"] for s in group),
            "skills_with_extra_files": sum(1 for s in group if s["extra_files"] > 0),
            "skills_skill_md_only": sum(1 for s in group if s["extra_files"] == 0),
            "max_skill_md": max(({"name": s["name"], "bytes": s["skill_md_bytes"]} for s in group), key=lambda x: x["bytes"], default=None),
            "min_skill_md": min(({"name": s["name"], "bytes": s["skill_md_bytes"]} for s in group), key=lambda x: x["bytes"], default=None),
            "median_skill_md_bytes": statistics.median([s["skill_md_bytes"] for s in group]) if group else None,
            "max_total": max(({"name": s["name"], "bytes": s["total_bytes"], "files": s["total_files"]} for s in group), key=lambda x: x["bytes"], default=None),
        }
    sys_g = [s for s in valid if s["kind"] == "system"]
    cus_g = [s for s in valid if s["kind"] == "custom"]
    subdir_counter = Counter()
    for s in valid:
        for sd in s["subdirs"]:
            subdir_counter[sd] += 1
    out = {
        "roots": {k: str(v) for k, v in ROOTS.items()},
        "total_skill_dirs": len(skills),
        "skills_with_skill_md": len(valid),
        "skills_without_skill_md": [s["name"] for s in skills if not s.get("has_skill_md")],
        "read_errors": errors,
        "system": agg(sys_g), "custom": agg(cus_g), "all": agg(valid),
        "fm_name_present_count": sum(1 for s in valid if s["fm_name"]),
        "h1_present_count": sum(1 for s in valid if s["has_h1"]),
        "skill_yaml_present_count": sum(1 for s in valid if s["has_skill_yaml"]),
        "skill_yaml_missing": [s["name"] for s in valid if not s["has_skill_yaml"]],
        "fm_name_missing": [s["name"] for s in valid if not s["fm_name"]],
        "fm_description_missing": [s["name"] for s in valid if not s["fm_description"]],
        "nested_skill_md_total": sum(s["nested_skill_md"] for s in valid),
        "nested_skill_md_in": [s["name"] for s in valid if s["nested_skill_md"] > 0],
        "top_subdirs": subdir_counter.most_common(15),
        "extensions": ext_counter.most_common(20),
        "total_files_all_roots": total_files_all,
        "email_pattern_count_only": {"matches": email_count, "files": email_files},
        "skills": valid,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
