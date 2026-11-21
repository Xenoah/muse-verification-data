#!/usr/bin/env python3
import base64, json, subprocess, sys, tempfile
from pathlib import Path
HELPER = Path.home() / "workspace/custom-connectors/custom.openai/bin/openai_call.py"
BASE = ("Flat minimal vector-style infographic diagram, dark slate background, "
        "teal and warm orange color palette, clean boxes and arrows, large clear sans-serif labels. "
        "Use ONLY the exact English labels and numbers listed, spelled exactly as given, no other text, no Japanese text.")
DIAGRAMS = {
 "diagram1-flow.png": BASE + " Horizontal flow diagram with three stages left to right connected by arrows. "
   "Left box title: 'Nov 15 snapshot' with two lines inside: 'Total: 86' and 'Done 2 / Pending 84'. "
   "Middle box title: 'Inflow in 5 days: +16' with two lines inside: 'New public repos: 4' and 'Existing private repos: 12'. "
   "Right box title: 'Nov 20 snapshot' with two lines inside: 'Total: 102' and 'Done 6 / Pending 96'. "
   "One additional small label under the middle box: 'Deleted: 0'.",
 "diagram2-forecast.png": BASE + " Vertical numbered procedure diagram with five steps top to bottom connected by downward arrows. "
   "Step boxes labeled exactly: '1 Snapshot the queue twice', '2 Compare by full repo name', '3 Split inflow by creation date', '4 Recalculate the forecast date', '5 Compare with previous forecast'. "
   "One side label box: 'Forecast delay: 17 days'.",
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
