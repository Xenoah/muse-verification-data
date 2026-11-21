#!/usr/bin/env python3
"""Paper 016: full-population inventory of Muse's Spaces (web artifacts).
Catalog snapshot: artifact.list on 2026-11-18 (10 entries) embedded below.
Local trees: ~/workspace/ts-spaces/<slug>/ (build/source), ~/workspace/space_data/<slug>/,
~/workspace/space-versions/<slug>/. Structural data only: names, sizes, counts.
Email-pattern scan is COUNT ONLY (strings never output). Read-only.
"""
import os, re, json, statistics
from pathlib import Path
from collections import Counter

HOME = Path.home()
TS = HOME / "workspace/ts-spaces"
SD = HOME / "workspace/space_data"
SV = HOME / "workspace/space-versions"
EMAIL_RE = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

CATALOG = [
    {"slug": "2026", "name": "2026年 技術系イベント詳細", "placement": "library"},
    {"slug": "2026-2", "name": "2026年 技術系イベント詳細", "placement": "library"},
    {"slug": "chimera-zhao-huan-suo", "name": "CHIMERA 召喚所", "placement": "sidebar"},
    {"slug": "githubripozitorishao-jie-ji-shi", "name": "GitHubリポジトリ紹介記事", "placement": "sidebar"},
    {"slug": "hacksiyasuiji-zhong-diao-cha", "name": "Hackしやすい機種調査", "placement": "library"},
    {"slug": "lun-wen-sirizu-sutetasu", "name": "論文シリーズ・ステータス", "placement": "sidebar"},
    {"slug": "muse-mail-muse-ai-dedekirukoto", "name": "Muse Mail（@muse.ai）でできること", "placement": "library"},
    {"slug": "musio-ri-ci-bgm", "name": "Musio 日次BGM", "placement": "sidebar"},
    {"slug": "resitoshou-fu", "name": "レシート受付", "placement": "sidebar"},
    {"slug": "xin-zhao-aimoderu", "name": "新着AIモデル", "placement": "sidebar"},
]

def scan(root: Path):
    files = []
    errors = 0
    if not root.exists():
        return files, errors
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            fp = Path(dirpath) / fn
            try:
                sz = fp.stat().st_size
            except Exception:
                errors += 1
                continue
            files.append((fp.relative_to(root).as_posix(), sz))
    return files, errors

def main():
    errors = 0
    email_matches = 0
    email_files = 0
    per = []
    ts_dirs = sorted([d.name for d in TS.iterdir() if d.is_dir()]) if TS.exists() else []
    sd_dirs = sorted([d.name for d in SD.iterdir() if d.is_dir()]) if SD.exists() else []
    sv_dirs = sorted([d.name for d in SV.iterdir() if d.is_dir()]) if SV.exists() else []
    catalog_slugs = [c["slug"] for c in CATALOG]
    for slug in sorted(set(catalog_slugs) | set(ts_dirs) | set(sd_dirs)):
        root = TS / slug
        files, e = scan(root)
        errors += e
        total = sum(s for _, s in files)
        nm_files = [(n, s) for n, s in files if "node_modules" in Path(n).parts]
        top = Counter()
        top_bytes = Counter()
        for n, s in files:
            first = Path(n).parts[0] if Path(n).parts else ""
            top[first] += 1
            top_bytes[first] += s
        ext = Counter(Path(n).suffix.lower() or "(none)" for n, _ in files)
        ext_bytes = Counter()
        for n, s in files:
            ext_bytes[Path(n).suffix.lower() or "(none)"] += s
        largest = max(files, key=lambda x: x[1]) if files else None
        # email scan: .md/.ts/.tsx/.js/.json source files outside node_modules, count only
        for n, s in files:
            if "node_modules" in Path(n).parts:
                continue
            if Path(n).suffix.lower() in (".md", ".ts", ".tsx", ".js", ".json", ".html"):
                try:
                    m = EMAIL_RE.findall((root / n).read_bytes())
                    if m:
                        email_matches += len(m); email_files += 1
                except Exception:
                    errors += 1
        sd_files, e2 = scan(SD / slug); errors += e2
        sv_files, e3 = scan(SV / slug); errors += e3
        cat = next((c for c in CATALOG if c["slug"] == slug), None)
        per.append({
            "slug": slug,
            "in_catalog": cat is not None,
            "placement": cat["placement"] if cat else None,
            "ts_files": len(files), "ts_bytes": total,
            "node_modules_files": len(nm_files), "node_modules_bytes": sum(s for _, s in nm_files),
            "non_nm_files": len(files) - len(nm_files), "non_nm_bytes": total - sum(s for _, s in nm_files),
            "top_subdirs_by_bytes": [{"name": k, "files": top[k], "bytes": v} for k, v in top_bytes.most_common(6)],
            "ext_counts": dict(ext.most_common(12)),
            "ext_bytes": {k: ext_bytes[k] for k, _ in ext.most_common(12)},
            "largest_file": {"name": largest[0], "bytes": largest[1]} if largest else None,
            "space_data_files": len(sd_files), "space_data_bytes": sum(s for _, s in sd_files),
            "space_versions_files": len(sv_files), "space_versions_bytes": sum(s for _, s in sv_files),
            "in_space_data": slug in sd_dirs, "in_space_versions": slug in sv_dirs,
        })
    totals = [p["ts_bytes"] for p in per if p["in_catalog"]]
    nm_total = sum(p["node_modules_bytes"] for p in per)
    ts_total = sum(p["ts_bytes"] for p in per)
    out = {
        "read_errors": errors,
        "catalog": {"count": len(CATALOG), "sidebar": sum(1 for c in CATALOG if c["placement"] == "sidebar"),
                    "library": sum(1 for c in CATALOG if c["placement"] == "library"),
                    "duplicate_names": [n for n, c in Counter(c["name"] for c in CATALOG).items() if c > 1]},
        "ts_spaces_dirs": ts_dirs,
        "space_data_dirs": sd_dirs,
        "space_versions_dirs": sv_dirs,
        "orphans": {
            "in_ts_not_catalog": sorted(set(ts_dirs) - set(catalog_slugs)),
            "in_catalog_not_ts": sorted(set(catalog_slugs) - set(ts_dirs)),
            "in_space_data_not_catalog": sorted(set(sd_dirs) - set(catalog_slugs)),
            "in_space_versions_not_catalog": sorted(set(sv_dirs) - set(catalog_slugs)),
            "catalog_not_in_space_data": sorted(set(catalog_slugs) - set(sd_dirs)),
            "catalog_not_in_space_versions": sorted(set(catalog_slugs) - set(sv_dirs)),
        },
        "totals": {
            "ts_files_all_dirs": sum(p["ts_files"] for p in per),
            "ts_bytes_all_dirs": ts_total,
            "ts_files_catalog": sum(p["ts_files"] for p in per if p["in_catalog"]),
            "ts_bytes_catalog": sum(p["ts_bytes"] for p in per if p["in_catalog"]),
            "node_modules_files": sum(p["node_modules_files"] for p in per),
            "node_modules_bytes": nm_total,
            "node_modules_share_pct": round(100 * nm_total / ts_total, 2) if ts_total else None,
            "non_nm_bytes": ts_total - nm_total,
            "space_data_files_total": sum(p["space_data_files"] for p in per),
            "space_data_bytes_total": sum(p["space_data_bytes"] for p in per),
            "space_versions_files_total": sum(p["space_versions_files"] for p in per),
            "space_versions_bytes_total": sum(p["space_versions_bytes"] for p in per),
            "per_space_bytes_median_catalog": statistics.median(totals) if totals else None,
            "per_space_bytes_mean_catalog": round(statistics.mean(totals), 1) if totals else None,
        },
        "email_pattern_count_only_source": {"matches": email_matches, "files": email_files},
        "per_space": per,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
