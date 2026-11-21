import re, json, pathlib, unicodedata
files={
1: pathlib.Path.home()/"workspace/goals/note/files/paper-001-ai-model-space-audit.md",
2: pathlib.Path.home()/"workspace/goals/goal/files/paper-002-cpu-inference-benchmark.md",
3: pathlib.Path.home()/"workspace/goals/goal/files/paper-003-space-reaudit.md",
4: pathlib.Path.home()/"workspace/goals/goal/files/paper-004-agi-usefulness-case-study.md",
5: pathlib.Path.home()/"workspace/goals/goal/files/paper-005-personal-information.md",
6: pathlib.Path.home()/"workspace/goals/goal/files/paper-006-tsubuyai-editorial-audit.md",
7: pathlib.Path.home()/"workspace/goals/goal/files/paper-007-diary-pipeline-audit.md",
}
board={1:15392,2:11724,3:12458,4:10122,5:9010,6:5137,7:6305}
email_re=re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
out={}
for n,p in files.items():
    t=p.read_text(encoding='utf-8') if p.exists() else ""
    heads=re.findall(r'第[一二三四五六七八九十0-9]+章', t)
    disc={
      "not_formal": "正式な学術論文ではない" in t or "正式な学術論文ではありません" in t,
      "no_peer_review": "査読" in t,
      "author_muse": "Muse" in t[:3000],
      "no_guarantee": "保証" in t[:3000],
      "rights": "権利者" in t[:3000] or "各権利" in t,
    }
    out[n]={
      "exists": p.exists(), "path": str(p), "chars": len(t), "board_chars": board[n],
      "char_diff": len(t)-board[n] if p.exists() else None,
      "disclaimer": disc, "disclaimer_all": all(disc.values()),
      "chapter_headings": heads, "chapter_count": len(heads),
      "has_abstract": "要旨" in t, "has_method": "方法" in t, "has_result": "結果" in t,
      "has_discussion": "考察" in t, "has_limits": "限界" in t, "has_sources": ("出典" in t or "参考文献" in t or "資料" in t),
      "email_matches": email_re.findall(t),
      "email_count": len(email_re.findall(t)),
    }
print(json.dumps(out, ensure_ascii=False, indent=2))
pathlib.Path.home().joinpath("workspace/goals/goal/hidden_files/audit-008/audit-008-results.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
