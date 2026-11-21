#!/usr/bin/env python3
"""Audit 017: independent full enumeration of Musio BGM bulk-v3 production outputs.
Reads only primary artifacts: bulk-v3/*.zip, bulk-v3/manifest.json, queue.json.
Does not trust manifest aggregates; recomputes everything from the zips themselves.
"""
import json, zipfile, hashlib, subprocess, io, os, re, statistics, sys
from collections import Counter, defaultdict
from PIL import Image

BASE = os.path.expanduser("~/workspace/musio-bgm")
V3 = os.path.join(BASE, "bulk-v3")

def parse_midi(data):
    """Minimal SMF parser (format 0/1). Returns dict of measurements."""
    assert data[:4] == b"MThd"
    fmt, ntrk, ppq = int.from_bytes(data[8:10],'big'), int.from_bytes(data[10:12],'big'), int.from_bytes(data[12:14],'big')
    pos = 14
    events = []  # (abs_tick, type, channel, d1, d2)
    tempos = []  # (tick, us_per_quarter)
    max_tick = 0
    for _ in range(ntrk):
        assert data[pos:pos+4] == b"MTrk", data[pos:pos+4]
        tlen = int.from_bytes(data[pos+4:pos+8],'big')
        end = pos + 8 + tlen
        p = pos + 8
        tick = 0
        running = None
        while p < end:
            # delta time VLQ
            delta = 0
            while True:
                b = data[p]; p += 1
                delta = (delta << 7) | (b & 0x7F)
                if not (b & 0x80): break
            tick += delta
            max_tick = max(max_tick, tick)
            status = data[p]
            if status == 0xFF:
                running = None
                mtype = data[p+1]
                # length VLQ
                q = p + 2; ln = 0
                while True:
                    b = data[q]; q += 1
                    ln = (ln << 7) | (b & 0x7F)
                    if not (b & 0x80): break
                if mtype == 0x51 and ln == 3:
                    tempos.append((tick, int.from_bytes(data[q:q+3],'big')))
                p = q + ln
            elif status in (0xF0, 0xF7):
                running = None
                q = p + 1; ln = 0
                while True:
                    b = data[q]; q += 1
                    ln = (ln << 7) | (b & 0x7F)
                    if not (b & 0x80): break
                p = q + ln
            else:
                if status & 0x80:
                    running = status; p += 1
                else:
                    status = running
                hi = status & 0xF0; ch = status & 0x0F
                if hi in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    d1, d2 = data[p], data[p+1]; p += 2
                    events.append((tick, hi, ch, d1, d2))
                elif hi in (0xC0, 0xD0):
                    p += 1
        pos = end
    return {"format": fmt, "ntrk": ntrk, "ppq": ppq, "tempos": tempos,
            "events": events, "max_tick": max_tick}

def midi_duration_and_kick(m):
    ppq = m["ppq"]
    tempos = sorted(m["tempos"]) or [(0, 500000)]
    # duration: integrate tempo map to max_tick
    total_us = 0.0
    prev_tick, prev_tempo = 0, tempos[0][1]
    for t, tempo in tempos[1:]:
        total_us += (t - prev_tick) * prev_tempo / ppq
        prev_tick, prev_tempo = t, tempo
    total_us += (m["max_tick"] - prev_tick) * prev_tempo / ppq
    dur = total_us / 1e6
    # notes
    noteons = [e for e in m["events"] if e[1] == 0x90 and e[4] > 0]
    channels = Counter(e[2] for e in noteons)
    pitches = [e[3] for e in noteons if e[2] != 9]
    # kick analysis: drum channel 9, notes 35/36; bar = 4 quarters (4/4 assumed; no time-sig events present)
    bar_ticks = 4 * ppq
    sixteenth = ppq // 4
    kick_ticks = sorted(e[0] for e in noteons if e[2] == 9 and e[3] in (35, 36))
    drum_ticks = [e[0] for e in noteons if e[2] == 9]
    bars_with_drum = set(t // bar_ticks for t in drum_ticks)
    bars_with_kick = set(t // bar_ticks for t in kick_ticks)
    four_floor_bars = 0
    for bar in bars_with_kick:
        steps = set()
        for t in kick_ticks:
            if t // bar_ticks == bar:
                off = t - bar * bar_ticks
                # quantize to nearest 16th step
                step = round(off / sixteenth)
                if abs(off - step * sixteenth) <= sixteenth // 4:
                    steps.add(step % 16)
        if {0, 4, 8, 12} <= steps:
            four_floor_bars += 1
    total_bars = m["max_tick"] // bar_ticks + (1 if m["max_tick"] % bar_ticks else 0)
    return {
        "midi_duration_sec": round(dur, 3),
        "noteons": len(noteons),
        "channels_used": sorted(channels.keys()),
        "n_channels": len(channels),
        "pitch_min": min(pitches) if pitches else None,
        "pitch_max": max(pitches) if pitches else None,
        "drum_noteons": len(drum_ticks),
        "kick_noteons": len(kick_ticks),
        "total_bars": total_bars,
        "bars_with_drum": len(bars_with_drum),
        "bars_with_kick": len(bars_with_kick),
        "four_floor_bars": four_floor_bars,
        "tempos": m["tempos"],
    }

def ffprobe_mp3(path_bytes_io_name):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration,bit_rate", "-show_entries",
                          "stream=codec_name,sample_rate,channels,bit_rate",
                          "-of", "json", path_bytes_io_name],
                         capture_output=True, text=True)
    return json.loads(out.stdout)

def volumedetect(zip_path):
    # extract mp3 to temp via zipfile read -> pipe to ffmpeg stdin
    with zipfile.ZipFile(zip_path) as z:
        mp3 = z.read("track.mp3")
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", "pipe:0", "-af", "volumedetect", "-f", "null", "-"],
                       input=mp3, capture_output=True)
    txt = p.stderr.decode(errors="replace")
    mx = re.search(r"max_volume:\s*(-?[\d.]+) dB", txt)
    mean = re.search(r"mean_volume:\s*(-?[\d.]+) dB", txt)
    return (float(mx.group(1)) if mx else None, float(mean.group(1)) if mean else None)

def main():
    manifest = json.load(open(os.path.join(V3, "manifest.json")))
    queue = json.load(open(os.path.join(BASE, "queue.json")))
    man_by_qid = {t["queue_id"]: t for t in manifest["tracks"]}
    queue_by_id = {q["id"]: q for q in queue}
    zips = sorted(f for f in os.listdir(V3) if f.endswith(".zip"))
    results = {"zip_count": len(zips), "tracks": [], "errors": []}
    for zname in zips:
        zpath = os.path.join(V3, zname)
        rec = {"zip": zname, "zip_size_disk": os.path.getsize(zpath)}
        try:
            with zipfile.ZipFile(zpath) as z:
                bad = z.testzip()
                rec["crc_ok"] = bad is None
                names = sorted(z.namelist())
                rec["contents"] = names
                sizes = {n: z.getinfo(n).file_size for n in names}
                rec["member_sizes"] = sizes
                tj = json.loads(z.read("track.json"))
                rec["track_json"] = tj
                mid = z.read("track.mid")
                rec["mid_sha256_inzip"] = hashlib.sha256(mid).hexdigest()
                rec["mid_size"] = len(mid)
                m = parse_midi(mid)
                rec["midi"] = midi_duration_and_kick(m)
                rec["midi_format"] = m["format"]; rec["midi_ppq"] = m["ppq"]
                cover = z.read("cover.jpg")
                im = Image.open(io.BytesIO(cover))
                rec["cover"] = {"format": im.format, "size_px": list(im.size), "bytes": len(cover)}
            # ffprobe via temp file
            tmp = "/tmp/audit017_track.mp3"
            with zipfile.ZipFile(zpath) as z:
                open(tmp, "wb").write(z.read("track.mp3"))
            fp = ffprobe_mp3(tmp)
            st = fp["streams"][0]
            rec["mp3"] = {"duration": float(fp["format"]["duration"]),
                          "format_bit_rate": int(fp["format"]["bit_rate"]),
                          "codec": st["codec_name"], "sample_rate": int(st["sample_rate"]),
                          "channels": st["channels"]}
            mx, mean = volumedetect(zpath)
            rec["mp3"]["max_volume_db"] = mx; rec["mp3"]["mean_volume_db"] = mean
            # cross-checks
            qid = int(zname.split("-")[0])
            rec["queue_id"] = qid
            man = man_by_qid.get(qid); q = queue_by_id.get(qid)
            rec["manifest_found"] = man is not None
            if man:
                rec["check_zip_size_manifest"] = (rec["zip_size_disk"] == man["zip_size"])
                rec["check_mid_sha_manifest"] = (rec["mid_sha256_inzip"] == man["song_mid_sha256"])
                rec["check_contents_manifest"] = (names == sorted(man["zip_contents"]))
                rec["manifest_duration"] = man["duration_sec"]
                rec["duration_diff_ffprobe_minus_manifest"] = round(rec["mp3"]["duration"] - man["duration_sec"], 3)
                rec["intent"] = man["intent"]
                rec["check_title_manifest_vs_trackjson"] = (man["title"] == tj["title"])
                rec["check_bpm_manifest_vs_trackjson"] = (man["bpm"] == tj["bpm"])
                rec["check_key_manifest_vs_trackjson"] = (man["key"] == tj["key"])
                rec["check_genre_manifest_vs_trackjson"] = (man["genre"] == tj["genre"])
            if q:
                rec["check_title_queue_vs_trackjson"] = (q["title"] == tj["title"])
                rec["check_bpm_queue_vs_trackjson"] = (q["bpm"] == tj["bpm"])
                rec["check_key_queue_vs_trackjson"] = (q["key"] == tj["key"])
                rec["check_genre_queue_vs_trackjson"] = (q["genre"] == tj["genre"])
                rec["queue_done"] = q.get("done")
        except Exception as e:
            rec["error"] = repr(e)
            results["errors"].append({"zip": zname, "error": repr(e)})
        results["tracks"].append(rec)
    # aggregates
    tr = [t for t in results["tracks"] if "mp3" in t]
    durs = [t["mp3"]["duration"] for t in tr]
    agg = {
        "n_ok": len(tr),
        "total_duration_sec": round(sum(durs), 1),
        "duration_min": min(durs), "duration_max": max(durs),
        "duration_median": statistics.median(durs), "duration_mean": round(statistics.mean(durs), 2),
        "n_under_120s": sum(1 for d in durs if d < 120),
        "n_under_138s": sum(1 for d in durs if d < 138),
        "all_contents_exact4": all(t["contents"] == ["cover.jpg", "track.json", "track.mid", "track.mp3"] for t in tr),
        "all_crc_ok": all(t["crc_ok"] for t in tr),
        "all_mid_sha_match": all(t.get("check_mid_sha_manifest") for t in tr),
        "all_zip_size_match": all(t.get("check_zip_size_manifest") for t in tr),
        "all_trackjson_match_manifest": all(t.get("check_title_manifest_vs_trackjson") and t.get("check_bpm_manifest_vs_trackjson") and t.get("check_key_manifest_vs_trackjson") and t.get("check_genre_manifest_vs_trackjson") for t in tr),
        "all_trackjson_match_queue": all(t.get("check_title_queue_vs_trackjson") and t.get("check_bpm_queue_vs_trackjson") and t.get("check_key_queue_vs_trackjson") and t.get("check_genre_queue_vs_trackjson") for t in tr),
        "intent_counts": dict(Counter(t.get("intent") for t in tr)),
        "total_zip_bytes": sum(t["zip_size_disk"] for t in tr),
        "total_mp3_bytes": sum(t["member_sizes"]["track.mp3"] for t in tr),
        "total_mid_bytes": sum(t["member_sizes"]["track.mid"] for t in tr),
        "mp3_codecs": dict(Counter(t["mp3"]["codec"] for t in tr)),
        "mp3_sample_rates": dict(Counter(t["mp3"]["sample_rate"] for t in tr)),
        "mp3_bitrates": dict(Counter(t["mp3"]["format_bit_rate"] for t in tr)),
        "cover_formats": dict(Counter(t["cover"]["format"] for t in tr)),
        "cover_sizes_px": dict(Counter("x".join(str(v) for v in t["cover"]["size_px"]) for t in tr)),
        "silent_tracks_maxvol_le_-60": [t["zip"] for t in tr if (t["mp3"]["max_volume_db"] is not None and t["mp3"]["max_volume_db"] <= -60)],
        "maxvol_min": min(t["mp3"]["max_volume_db"] for t in tr if t["mp3"]["max_volume_db"] is not None),
        "maxvol_max": max(t["mp3"]["max_volume_db"] for t in tr if t["mp3"]["max_volume_db"] is not None),
        "four_floor_total_bars_with_drum": sum(t["midi"]["bars_with_drum"] for t in tr),
        "four_floor_total_bars": sum(t["midi"]["four_floor_bars"] for t in tr),
        "tracks_over40pct_fourfloor": [{"zip": t["zip"], "ff": t["midi"]["four_floor_bars"], "drum_bars": t["midi"]["bars_with_drum"],
                                        "ratio": round(t["midi"]["four_floor_bars"]/t["midi"]["bars_with_drum"], 3) if t["midi"]["bars_with_drum"] else None}
                                       for t in tr if t["midi"]["bars_with_drum"] and t["midi"]["four_floor_bars"]/t["midi"]["bars_with_drum"] > 0.40],
        "tracks_no_drums": [t["zip"] for t in tr if t["midi"]["bars_with_drum"] == 0],
        "duration_diff_abs_max": max(abs(t["duration_diff_ffprobe_minus_manifest"]) for t in tr),
        "midi_vs_mp3_duration_diff_abs_max": max(abs(t["midi"]["midi_duration_sec"] - t["mp3"]["duration"]) for t in tr),
        "produced_dates": dict(Counter(man_by_qid[t["queue_id"]]["produced_date"] for t in tr if t["queue_id"] in man_by_qid)),
        "manifest_status_counts": dict(Counter(t["status"] for t in manifest["tracks"])),
        "manifest_count": len(manifest["tracks"]),
        "queue_count": len(queue),
        "queue_done_count": sum(1 for q in queue if q.get("done")),
    }
    results["aggregates"] = agg
    json.dump(results, open(os.path.expanduser("~/workspace/goals/goal/hidden_files/audit-017/audit-017-results.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(agg, ensure_ascii=False, indent=1))
    if results["errors"]: print("ERRORS:", results["errors"])

if __name__ == "__main__":
    main()
