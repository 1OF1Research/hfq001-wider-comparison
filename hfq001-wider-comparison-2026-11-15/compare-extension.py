"""HFQ-001 wider comparison — EXTENSION harness (2026-11-15).

Runs the two cells proposed by Lawless1987 (topic 180706,
post #26) and registered in extension-predictions-2026-11-15.md
BEFORE this file was written:

  X1  post-pruning nonce reuse (HYB pruned / HYB unpruned /
      P6 control)
  X2  RP-enforced exp-iat cap (EXP and HYB), including X2d:
      the original suite's EXP/HYB W-cells re-run against the
      capped RP to prove no settled cell moves.

Everything except the two mechanisms under test is compare.py's
own code, imported unchanged: the byte layer, profile checks,
signature recovery, minting, and the RP verifier. The extension
adds exactly two things, both by subclassing compare.RP:

  PruningRP — the pair-store remembers each recorded pair's
              receipt exp, and prune(now) drops pairs whose
              exp has passed (the rule DESIGN.md states).
  CappedRP  — clause (d)'s time checks gain one rule: reject
              if exp - iat > CAP (CAP = 300 s, the suite's
              standard test window).

Nothing here posts or sends anything.
"""
import json, sys

sys.path.insert(0, ".")
sys.path.insert(0, "../hfq001-vectors-2026-11-14")
import compare as cmp

T0, WINDOW = cmp.T0, cmp.WINDOW
CAP = WINDOW  # the RP's published maximum window, per registration
NONCE_X1 = "dd04" * 8


class PruningRP(cmp.RP):
    """compare.RP plus the pruning rule DESIGN.md states for
    HYB: a recorded pair may be dropped once its receipt's exp
    has passed. The pre-parse below only reads the receipt's
    own exp so the store can remember it; verification itself
    is entirely the parent class's."""

    def __init__(self, shape):
        super().__init__(shape)
        self.pair_exp = {}
        self._pending_exp = None

    def present(self, receipt, signer_key, now):
        parsed = cmp.parse(receipt["input_json_text"])
        exp = parsed.get("exp")
        self._pending_exp = cmp.parse_time(exp) if exp else None
        return super().present(receipt, signer_key, now)

    def _stateful(self, addr, nonce):
        if (addr, nonce) in self.store:
            return "reject", "P6d replay of (signer, nonce)"
        self.store.add((addr, nonce))
        if self._pending_exp is not None:
            self.pair_exp[(addr, nonce)] = self._pending_exp
        return "accept", "accepted; (signer, nonce) recorded"

    def prune(self, now):
        for pair, exp in list(self.pair_exp.items()):
            if exp <= now:
                self.store.discard(pair)
                del self.pair_exp[pair]


class CappedRP(cmp.RP):
    """compare.RP with one added clause-(d) rule, evaluated
    inside the time checks: a window over the RP's published
    cap is rejected, the cap named as the cause."""

    def _time_checks(self, parsed, now):
        iat, exp = parsed.get("iat"), parsed.get("exp")
        if iat is not None and exp is not None and \
                cmp.parse_time(exp) - cmp.parse_time(iat) > CAP:
            return "reject", "clause (d): exp-iat window %ds " \
                             "exceeds RP cap %ds" % (
                                 cmp.parse_time(exp)
                                 - cmp.parse_time(iat), CAP)
        return super()._time_checks(parsed, now)


# --- run bookkeeping (compare.py's rec shape) ---
OUT = {"gate": None, "x1": {}, "x2": {}, "x2d": {}}
LOG = []


def rec(section, shape, case, expected, observed, agree, detail):
    OUT[section].setdefault(shape, []).append(
        {"case": case, "expected": expected, "observed": observed,
         "agree": agree, "detail": detail})
    LOG.append("%-5s %-28s exp=%-22s obs=%-22s %s :: %s"
               % (shape, case, expected, observed,
                  "AGREE" if agree else "DIVERGE", detail))


def seq_str(seq):
    return "/".join(seq)


def x1():
    # HYB receipts: R1 standard window; R2 same nonce, fresh window.
    r1 = cmp.mint(cmp.fields_for("HYB", NONCE_X1, "x1-first"))
    f2 = cmp.fields_for("HYB", NONCE_X1, "x1-second")
    f2["iat"] = cmp.rfc3339(T0 + 400)
    f2["exp"] = cmp.rfc3339(T0 + 700)
    r2 = cmp.mint(f2)
    # HYB, pruning exercised at the first licensed moment.
    rp = PruningRP("HYB")
    seq = [rp.present(r1, "A", T0 + 10)[0]]
    rp.prune(T0 + WINDOW + 1)
    v2, why2 = rp.present(r2, "A", T0 + 410)
    seq.append(v2)
    v3, why3 = rp.present(r1, "A", T0 + 410)
    seq.append(v3)
    rec("x1", "HYB", "X1-pruned-reuse", "accept/accept/reject",
        seq_str(seq), seq_str(seq) == "accept/accept/reject",
        "pair pruned at T0+301 (exp passed); new receipt reuses "
        "the nonce in a fresh window: %s; the OLD receipt again: "
        "%s" % (why2, why3))
    # HYB, unpruned control: same receipts, pair kept past exp.
    rp = PruningRP("HYB")
    seq = [rp.present(r1, "A", T0 + 10)[0],
           rp.present(r2, "A", T0 + 410)[0]]
    rec("x1", "HYB", "X1-unpruned-control", "accept/reject",
        seq_str(seq), seq_str(seq) == "accept/reject",
        "no pruning taken; isolates pruning as the cause of "
        "the pruned arm's second accept")
    # P6 control: no time fields, no pruning exists.
    rp = cmp.RP("P6")
    p1 = cmp.mint(cmp.fields_for("P6", NONCE_X1, "x1-first"))
    p2 = cmp.mint(cmp.fields_for("P6", NONCE_X1, "x1-second"))
    seq = [rp.present(p1, "A", T0 + 10)[0],
           rp.present(p2, "A", T0 + 410)[0]]
    rec("x1", "P6", "X1-p6-control", "accept/reject",
        seq_str(seq), seq_str(seq) == "accept/reject",
        "P6 keeps every pair; a new receipt reusing the nonce "
        "is refused on the recorded pair")


def x2():
    for shape in ("EXP", "HYB"):
        # X2a at the cap: the standard window, 300 = CAP.
        rp = CappedRP(shape)
        r = cmp.mint(cmp.fields_for(shape, "ee05" * 8, "x2a"))
        v, why = rp.present(r, "A", T0 + 10)
        rec("x2", shape, "X2a-at-cap", "accept", v, v == "accept",
            "exp-iat = 300 = CAP; exceeds is strict :: " + why)
        # X2b one second over.
        rp = CappedRP(shape)
        f = cmp.fields_for(shape, "ee06" * 8, "x2b")
        f["exp"] = cmp.rfc3339(T0 + WINDOW + 1)
        v, why = rp.present(cmp.mint(f), "A", T0 + 10)
        rec("x2", shape, "X2b-one-over", "reject", v,
            v == "reject" and "cap" in why,
            "exp-iat = 301 > CAP, presented inside its window :: "
            + why)
        if shape == "HYB":
            held = (cmp.ADDR["A"], "ee06" * 8) in rp.store
            rec("x2", shape, "X2b-store-untouched", "absent",
                "present" if held else "absent", not held,
                "a cap rejection records no pair (state changes "
                "only on accept)")
        # X2c the dishonest window: 30 days.
        rp = CappedRP(shape)
        f = cmp.fields_for(shape, "ee07" * 8, "x2c")
        f["exp"] = cmp.rfc3339(T0 + 30 * 86400)
        v, why = rp.present(cmp.mint(f), "A", T0 + 10)
        rec("x2", shape, "X2c-long-window", "reject", v,
            v == "reject" and "cap" in why,
            "exp-iat = 30 days > CAP :: " + why)


def x2d(original):
    """The original suite's EXP/HYB W-cells against CappedRP.
    Registered prediction: every outcome identical to the
    uncapped run (results-run1.json), because every mint in
    the suite uses exp-iat = 300 = CAP."""
    def orig_obs(shape, case):
        for row in original["w"][shape]:
            if row["case"] == case:
                return row["observed"]
        raise KeyError(case)

    def check(shape, case, observed):
        exp = orig_obs(shape, case)
        rec("x2d", shape, case, exp, observed, observed == exp,
            "capped RP vs uncapped results-run1.json")

    for shape in ("EXP", "HYB"):
        rp = CappedRP(shape)
        r = cmp.mint(cmp.fields_for(shape, cmp.NONCE1, "w01"))
        check(shape, "W01-in-window-replay", seq_str(
            [rp.present(r, "A", T0 + 10)[0],
             rp.present(r, "A", T0 + 20)[0]]))
        rp = CappedRP(shape)
        r = cmp.mint(cmp.fields_for(shape, cmp.NONCE1, "w02"))
        check(shape, "W02-post-window-replay", seq_str(
            [rp.present(r, "A", T0 + 10)[0],
             rp.present(r, "A", T0 + WINDOW + 1)[0]]))
        got = []
        for now in (T0 + WINDOW - 1, T0 + WINDOW):
            rp = CappedRP(shape)
            r = cmp.mint(cmp.fields_for(shape, cmp.NONCE1, "w07"))
            got.append(rp.present(r, "A", now)[0])
        check(shape, "W07-expiry-boundary", seq_str(got))
    rp = CappedRP("HYB")
    r = cmp.mint(cmp.fields_for("HYB", cmp.NONCE1, "w06"))
    seq = [rp.present(r, "A", T0 + 10)[0]]
    rp.wipe()
    seq.append(rp.present(r, "A", T0 + 20)[0])
    rp.wipe()
    seq.append(rp.present(r, "A", T0 + WINDOW + 1)[0])
    check("HYB", "W06-state-loss+expiry", seq_str(seq))
    rp = CappedRP("EXP")
    r = cmp.mint(cmp.fields_for("EXP", cmp.NONCE1, "w08"))
    check("EXP", "W08i-skew-behind", rp.present(r, "A", T0 - 120)[0])
    check("EXP", "W08ii-skew-ahead",
          rp.present(r, "A", T0 + WINDOW + 30)[0])
    rp = CappedRP("EXP")
    f = cmp.fields_for("EXP", cmp.NONCE1, "w09a")
    f.pop("exp")
    check("EXP", "W09a-no-exp", rp.present(cmp.mint(f), "A", T0 + 10)[0])
    f = cmp.fields_for("EXP", cmp.NONCE1, "w09b")
    f.pop("iat")
    check("EXP", "W09b-no-iat", rp.present(cmp.mint(f), "A", T0 + 10)[0])
    rp = CappedRP("HYB")
    f = cmp.fields_for("HYB", cmp.NONCE1, "w09c")
    f.pop("exp")
    check("HYB", "W09c-hyb-no-exp",
          rp.present(cmp.mint(f), "A", T0 + 10)[0])
    rp = CappedRP("HYB")
    r = cmp.mint(cmp.fields_for("HYB", cmp.NONCE1, "w12"))
    check("HYB", "W12-long-lived-replay", seq_str(
        [rp.present(r, "A", T0 + 10)[0],
         rp.present(r, "A", T0 + 30 * 86400)[0]]))


def main():
    ok, lines = cmp.orig.selfcheck()
    OUT["gate"] = lines
    LOG.extend(lines)
    if not ok:
        print("GATE FAILED — run does not start.")
        return 1
    with open("results-run1.json", encoding="utf-8") as fh:
        original = json.load(fh)
    x1()
    x2()
    x2d(original)
    print("\n".join(LOG))
    out_name = sys.argv[1] if len(sys.argv) > 1 else "extension-results.json"
    with open(out_name, "w", encoding="utf-8") as fh:
        json.dump(OUT, fh, ensure_ascii=False, indent=1,
                  sort_keys=True)
    bad = []
    for section in ("x1", "x2", "x2d"):
        for shape, rows in OUT[section].items():
            for r in rows:
                if not r["agree"]:
                    bad.append("%s/%s/%s" % (section, shape,
                                             r["case"]))
    print("\nDIVERGENCES from registered predictions: %s"
          % (", ".join(bad) if bad else "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
