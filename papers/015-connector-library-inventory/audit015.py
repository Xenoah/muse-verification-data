#!/usr/bin/env python3
"""Paper 015: full-population inventory of Muse's connector library.
System connectors: /opt/hatch/connectors/<name>/ (CONNECTOR.md, connector.yaml, manifest.yaml, extras).
Custom connectors: ~/workspace/custom-connectors/ (census only).
Structural data only: file names, sizes, line counts, YAML parseability, top-level key NAMES.
Email-pattern scan is COUNT ONLY (strings never output). Read-only except printing JSON.
"""
import os, re, json, statistics
from pathlib import Path
from collections import Counter

try:
    import yaml
except Exception:
    yaml = None

HOME = Path.home()
SYS = Path("/opt/hatch/connectors")
CUSTOM = HOME / "workspace/custom-connectors"
EMAIL_RE = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def lines_of(p):
    try:
        data = p.read_bytes()
        return len(data), data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
    except Exception:
        return 0, 0

def yaml_info(p):
    """Return (parse_ok, top_level_key_count). Key names are not stored."""
    if yaml is None:
        return None, None
    try:
        doc = yaml.safe_load(p.read_text(errors="replace"))
        if isinstance(doc, dict):
            return True, len(doc)
        return True, 0
    except Exception:
        return False, None

def main():
    errors = 0
    email_matches = 0
    email_files = 0
    per = []
    dirs = sorted([d for d in SYS.iterdir() if d.is_dir()], key=lambda x: x.name)
    for d in dirs:
        files = []
        for dirpath, dirnames, filenames in os.walk(d):
            for fn in filenames:
                fp = Path(dirpath) / fn
                try:
                    sz = fp.stat().st_size
                except Exception:
                    errors += 1
                    continue
                files.append({"name": fp.relative_to(d).as_posix(), "bytes": sz, "suffix": fp.suffix})
                if fp.suffix == ".md":
                    try:
                        em = EMAIL_RE.findall(fp.read_bytes())
                        if em:
                            email_matches += len(em); email_files += 1
                    except Exception:
                        errors += 1
        names = [f["name"] for f in files]
        cm = d / "CONNECTOR.md"; cy = d / "connector.yaml"; mf = d / "manifest.yaml"
        cm_b, cm_l = lines_of(cm) if cm.exists() else (0, 0)
        cy_ok, cy_keys = yaml_info(cy) if cy.exists() else (None, None)
        mf_ok, mf_keys = yaml_info(mf) if mf.exists() else (None, None)
        extra_md = [f for f in files if f["suffix"] == ".md" and f["name"] != "CONNECTOR.md"]
        scripts = [f for f in files if f["suffix"] in (".sh", ".py")]
        per.append({
            "name": d.name,
            "n_files": len(files),
            "total_bytes": sum(f["bytes"] for f in files),
            "has_connector_md": cm.exists(),
            "connector_md_bytes": cm_b, "connector_md_lines": cm_l,
            "has_connector_yaml": cy.exists(), "connector_yaml_parse_ok": cy_ok, "connector_yaml_top_keys": cy_keys,
            "has_manifest_yaml": mf.exists(), "manifest_yaml_parse_ok": mf_ok, "manifest_yaml_top_keys": mf_keys,
            "extra_md_count": len(extra_md), "extra_md_bytes": sum(f["bytes"] for f in extra_md),
            "extra_md_names": sorted(f["name"] for f in extra_md),
            "script_count": len(scripts), "script_names": sorted(f["name"] for f in scripts),
            "file_names": sorted(names),
        })
    # custom connectors census
    custom_dirs = []
    custom_files = 0
    if CUSTOM.exists():
        custom_dirs = sorted([d.name for d in CUSTOM.iterdir() if d.is_dir()])
        for dirpath, dirnames, filenames in os.walk(CUSTOM):
            custom_files += len(filenames)
    cm_sizes = [p["connector_md_bytes"] for p in per]
    totals = [p["total_bytes"] for p in per]
    extra_sorted = sorted(per, key=lambda x: -x["extra_md_count"])
    size_sorted = sorted(per, key=lambda x: -x["total_bytes"])
    out = {
        "system_root": str(SYS),
        "read_errors": errors,
        "connectors": {
            "count": len(per),
            "total_files": sum(p["n_files"] for p in per),
            "total_bytes": sum(totals),
            "with_connector_md": sum(1 for p in per if p["has_connector_md"]),
            "with_connector_yaml": sum(1 for p in per if p["has_connector_yaml"]),
            "with_manifest_yaml": sum(1 for p in per if p["has_manifest_yaml"]),
            "missing_manifest": sorted(p["name"] for p in per if not p["has_manifest_yaml"]),
            "connector_yaml_parse_ok": sum(1 for p in per if p["connector_yaml_parse_ok"] is True),
            "connector_yaml_parse_ng": sorted(p["name"] for p in per if p["connector_yaml_parse_ok"] is False),
            "manifest_yaml_parse_ok": sum(1 for p in per if p["manifest_yaml_parse_ok"] is True),
            "manifest_yaml_parse_ng": sorted(p["name"] for p in per if p["manifest_yaml_parse_ok"] is False),
            "exactly_3_files": sum(1 for p in per if p["n_files"] == 3),
            "with_extra_md": sum(1 for p in per if p["extra_md_count"] > 0),
            "extra_md_total": sum(p["extra_md_count"] for p in per),
            "extra_md_bytes_total": sum(p["extra_md_bytes"] for p in per),
            "with_scripts": sorted(p["name"] for p in per if p["script_count"] > 0),
            "script_total": sum(p["script_count"] for p in per),
            "suffix_counts": dict(Counter(f["suffix"] for p in per for f in [{"suffix": Path(n).suffix} for n in p["file_names"]])),
        },
        "connector_md": {
            "bytes_total": sum(cm_sizes),
            "bytes_median": statistics.median(cm_sizes) if cm_sizes else None,
            "bytes_mean": round(statistics.mean(cm_sizes), 1) if cm_sizes else None,
            "bytes_max": max(({"name": p["name"], "bytes": p["connector_md_bytes"]} for p in per), key=lambda x: x["bytes"], default=None),
            "bytes_min": min(({"name": p["name"], "bytes": p["connector_md_bytes"]} for p in per), key=lambda x: x["bytes"], default=None),
            "lines_total": sum(p["connector_md_lines"] for p in per),
        },
        "per_connector_total_bytes": {
            "median": statistics.median(totals) if totals else None,
            "max": size_sorted[0] if size_sorted else None,
            "top5": [{"name": p["name"], "bytes": p["total_bytes"], "files": p["n_files"]} for p in size_sorted[:5]],
            "top5_bytes_share_pct": round(100 * sum(p["total_bytes"] for p in size_sorted[:5]) / sum(totals), 2) if totals else None,
        },
        "extra_md_top": [{"name": p["name"], "extra_md_count": p["extra_md_count"], "extra_md_bytes": p["extra_md_bytes"]} for p in extra_sorted if p["extra_md_count"] > 0],
        "email_pattern_count_only_md": {"matches": email_matches, "files": email_files},
        "custom_connectors": {"root": str(CUSTOM), "dirs": custom_dirs, "dir_count": len(custom_dirs), "total_files": custom_files},
        "per_connector": per,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
