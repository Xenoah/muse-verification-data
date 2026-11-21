import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure as M

OUT = M.OUT
RES_PATH = os.path.join(OUT, "results_incremental.json")
RAW_PATH = os.path.join(OUT, "raw_outputs.json")

def load_res():
    if os.path.exists(RES_PATH):
        return json.load(open(RES_PATH))
    return {"questions": [], "main": {}, "stability": {}, "sensitivity": {}}

def save_res(res):
    json.dump(res, open(RES_PATH, "w"), ensure_ascii=False, indent=1)

def ensure_questions(res):
    if not res["questions"]:
        res["questions"] = [{"id": q[0], "question": q[1], "correct": q[2], "principle_keys": q[3]} for q in M.QUESTIONS]

def qmap():
    return {q[0]: q for q in M.QUESTIONS}

def do_main(res, qid):
    q = qmap()[qid]
    _, qtext, correct, keys = q
    a = M.cond_a(qtext, tag=qid + "-A-main")
    a["correct_flag"] = (a["answer"] == correct)
    b = M.cond_b(qtext, tag=qid + "-B-main")
    b["correct_flag"] = (b["answer"] == correct)
    b["principle_hits"] = M.principle_ok(b["principles"], keys)
    b["principle_ok"] = len(b["principle_hits"]) >= 1
    res["main"][qid] = {"A": a, "B": b}
    print(qid, "A", a["answer"], a["correct_flag"], "| B", b["answer"], b["correct_flag"], "| princ", b["principle_hits"], flush=True)

def do_stab(res, qid):
    q = qmap()[qid]
    _, qtext, correct, keys = q
    lst = []
    for rep in range(2):
        a = M.cond_a(qtext, tag=f"{qid}-A-stab{rep}")
        b = M.cond_b(qtext, tag=f"{qid}-B-stab{rep}")
        lst.append({"rep": rep, "A_answer": a["answer"], "A_correct": a["answer"] == correct, "B_answer": b["answer"], "B_correct": b["answer"] == correct, "B_principles": b["principles"]})
        print(qid, "stab", rep, "A", a["answer"], "B", b["answer"], flush=True)
    res["stability"][qid] = lst

def do_sens(res, qid):
    q = qmap()[qid]
    _, qtext, correct, keys = q
    alist, blist = [], []
    for s in range(5):
        a = M.cond_a(qtext, temp=0.7, seed=100 + s, tag=f"{qid}-A-sens{s}")
        alist.append({"seed": 100 + s, "answer": a["answer"], "correct": a["answer"] == correct, "gen": a["gen"]})
        b = M.cond_b(qtext, temp=0.7, seed=100 + s, tag=f"{qid}-B-sens{s}")
        blist.append({"seed": 100 + s, "answer": b["answer"], "correct": b["answer"] == correct, "principles": b["principles"], "principle_hits": M.principle_ok(b["principles"], keys), "gen": b["gen"]})
        print(qid, "sens", s, "A", a["answer"], "B", b["answer"], flush=True)
        res["sensitivity"][qid] = {"A": alist, "B": blist}
        save_res(res)

if __name__ == "__main__":
    # restore RAW log from previous partial run so raw_outputs.json stays complete
    if os.path.exists(RAW_PATH):
        try:
            M.RAW = json.load(open(RAW_PATH))
        except Exception:
            pass
    res = load_res()
    ensure_questions(res)
    mode, qid = sys.argv[1], sys.argv[2]
    if mode == "main":
        do_main(res, qid)
    elif mode == "stab":
        do_stab(res, qid)
    elif mode == "sens":
        do_sens(res, qid)
    save_res(res)
    json.dump(res, open(os.path.join(OUT, "results.json"), "w"), ensure_ascii=False, indent=1)
    print("DONE", mode, qid, flush=True)
