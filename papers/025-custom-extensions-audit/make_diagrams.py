#!/usr/bin/env python3
import base64, json, subprocess, sys, tempfile
from pathlib import Path
HELPER = Path.home() / "workspace/custom-connectors/custom.openai/bin/openai_call.py"
BASE = ("Flat minimal vector-style infographic diagram, dark slate background, "
        "teal and warm orange color palette, clean boxes and arrows, large clear sans-serif labels. "
        "Use ONLY the exact English labels and numbers listed, spelled exactly as given, no other text, no Japanese text.")
DIAGRAMS = {
 "diagram1-injection.png": BASE + " Comparison diagram with two columns. "
   "Left column title: 'Setting: include_in_prompt'. Left column boxes: 'true: 2 of 9', 'false: 7 of 9'. "
   "Right column title: 'Actually listed'. Right column boxes: 'Skills listed: 3 of 8', 'Listed despite false: 2'. "
   "Title at top: 'Setting vs actual listing'.",
 "diagram2-categories.png": BASE + " Horizontal bar chart of skill categories with five rows. "
   "Row 1 label: 'Writing' with value '3'. "
   "Row 2 label: 'Creation' with value '2'. "
   "Row 3 label: 'Personal planning' with value '1'. "
   "Row 4 label: 'Media' with value '1'. "
   "Row 5 label: 'Work and knowledge' with value '1'. "
   "Title at top: 'Learned skills by category (8 total)'. Bar lengths proportional to values.",
}
outdir = Path.home() / "workspace/goals/goal/hidden_files/illustrations/2026-11-23-025"
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
