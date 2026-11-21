#!/usr/bin/env python3
import base64, json, subprocess, sys, tempfile
from pathlib import Path
HELPER = Path.home() / "workspace/custom-connectors/custom.openai/bin/openai_call.py"
BASE = ("Flat minimal vector-style infographic diagram, dark slate background, "
        "teal and warm orange color palette, clean boxes and arrows, large clear sans-serif labels. "
        "Use ONLY the exact English labels and numbers listed, spelled exactly as given, no other text, no Japanese text.")
DIAGRAMS = {
 "diagram1-layers.png": BASE + " Horizontal three-layer audit flow diagram with three boxes left to right connected by arrows. "
   "Left box title: 'Source data' with two lines inside: 'projects.json' and 'Total: 108 items'. "
   "Middle box title: 'Generated pages' with two lines inside: 'Catalog: 108' and 'Sitemap URLs: 46'. "
   "Right box title: 'Repositories' with two lines inside: 'Types: 86' and 'External 85 + Own site 23 items'.",
 "diagram2-breakdown.png": BASE + " Breakdown diagram with one top box and two boxes below connected by lines. "
   "Top box: 'All projects: 108'. "
   "Left lower box title: 'With public site: 46' with one line inside: '42.59 percent'. "
   "Right lower box title: 'Without site: 62' with two lines inside: 'With reason: 62 of 62' and 'Top reason Firmware: 11'.",
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
