#!/usr/bin/env python3
import base64, json, subprocess, sys, tempfile
from pathlib import Path
HELPER = Path.home() / "workspace/custom-connectors/custom.openai/bin/openai_call.py"
BASE = ("Flat minimal vector-style infographic diagram, dark slate background, "
        "teal and warm orange color palette, clean boxes and arrows, large clear sans-serif labels. "
        "Use ONLY the exact English labels and numbers listed, spelled exactly as given, no other text, no Japanese text.")
DIAGRAMS = {
 "diagram1-strata.png": BASE + " Three horizontal bar rows comparing failure rates. "
   "Row 1 label: 'All 47 jobs' with bar value '0.71%'. "
   "Row 2 label: 'High-frequency jobs (100+ runs)' with bar value '0.40%'. "
   "Row 3 label: 'Other 42 jobs' with bar value '2.24%'. "
   "Title at top: 'Failure rate by job layer'.",
 "diagram2-failures.png": BASE + " Breakdown diagram with one top box and four boxes below connected by lines. "
   "Top box: '13 failures in total'. "
   "Box 1: 'AI model refresh (hourly): 6'. "
   "Box 2: 'AI paper explainer: 3'. "
   "Box 3: 'Repo article daily: 2'. "
   "Box 4: 'X diary collector: 2'. "
   "One separate small box at the side: 'Other 43 jobs: 0 failures'.",
}
outdir = Path.home() / "workspace/goals/goal/hidden_files/illustrations/2026-11-22-024"
outdir.mkdir(parents=True, exist_ok=True)
for name, prompt in DIAGRAMS.items():
    body = {"model":"gpt-image-1.5","prompt":prompt,"quality":"medium","size":"1536x1024"}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(body,f); bp=f.name
    p = subprocess.run([sys.executable, str(HELPER), "POST", "/v1/images/generations", "--body", bp], capture_output=True, text=True, timeout=300)
    if p.returncode!=0:
        print(name, "FAILED", p.stderr[:500]); sys.exit(1)
    resp=json.loads(p.stdout)
    data=base64.b64decode(resp["data"][0]["b64_json"])
    (outdir/name).write_bytes(data)
    print(name, len(data))
