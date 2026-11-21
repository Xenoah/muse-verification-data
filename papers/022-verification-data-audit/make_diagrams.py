#!/usr/bin/env python3
import base64, json, subprocess, sys, tempfile
from pathlib import Path
HELPER = Path.home() / "workspace/custom-connectors/custom.openai/bin/openai_call.py"
BASE = ("Flat minimal vector-style infographic diagram, dark slate background, "
        "teal and warm orange color palette, clean boxes and arrows, large clear sans-serif labels. "
        "Use ONLY the exact English labels and numbers listed, spelled exactly as given, no other text, no Japanese text.")
DIAGRAMS = {
 "diagram1-sync.png": BASE + " Horizontal three-box audit flow diagram left to right connected by arrows. "
   "Left box title: 'Local staging' with two lines inside: 'Files: 200' and 'Papers: 155 files'. "
   "Middle box title: 'Sync record' with two lines inside: 'Paths: 201' and 'Duplicate README: 1'. "
   "Right box title: 'Difference' with two lines inside: 'Unsynced: 0' and 'Stale: 0'.",
 "diagram2-completeness.png": BASE + " Breakdown diagram with one top box and two boxes below connected by lines. "
   "Top box: 'Paper folders: 20'. "
   "Left lower box title: 'With script: 16 of 20' with one line inside: 'With result JSON: 19 of 20'. "
   "Right lower box title: 'Paper 2 benchmark' with two lines inside: 'Files: 48' and 'Scripts: 0'.",
}
outdir = Path(__file__).parent / "diagrams"
outdir.mkdir(exist_ok=True)
for name, prompt in DIAGRAMS.items():
    body = {"model":"gpt-image-1.5","prompt":prompt,"quality":"medium","size":"1536x1024"}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(body,f); bp=f.name
    p = subprocess.run([sys.executable, str(HELPER), "POST", "/v1/images/generations", "--body", bp], capture_output=True, text=True, timeout=300)
    if p.returncode!=0:
        print(name, "FAILED", p.stderr[:400]); sys.exit(1)
    resp=json.loads(p.stdout)
    data=base64.b64decode(resp["data"][0]["b64_json"])
    (outdir/name).write_bytes(data)
    print(name, len(data), resp.get("usage"))
