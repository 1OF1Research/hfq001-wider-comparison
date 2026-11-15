# HFQ-001 — Wider comparison — VERDICT (2026-11-15)

State: **DERIVED.** One harness, one author. The harness is
independent of the counterparty (it reuses our own 2026-11-14
verifier's code for the shared layer) but not of the analyst;
an independent witness — a second implementation, or a stranger
re-running `compare.py` — is what would raise this. Design and
predictions were registered in DESIGN.md before any run. The
full suite ran twice; `results-run1.json` and
`results-run2.json` are byte-identical (51,580 B each).

## Verdict, plainly

**The hybrid beats P6 — narrowly, and in exactly one place.**
Nothing outside the family beats the family's core mechanism:
the durable (signer, nonce) pair-store survives every challenge
thrown at it. But P6 as adopted has one soft spot its own text
concedes and its vectors cannot test — it depends entirely on
that store never being lost, and a P6 receipt never expires.
The hybrid (P6 + signed iat/exp, pairs prunable after expiry)
keeps every P6 protection and closes the post-expiry half of
the state-loss hole. On the whole suite it never once accepts
something P6 rejects; it only converts wrong accepts into
rejects. The stateless shape is refuted as a replacement (it
accepts in-window replays). The challenge shape ties P6 on
protection and loses on shape: it makes a receipt interactive
and fails closed on restart.

## The outcome table (all runs firsthand, this folder)

Shared byte layer — the original 20 vectors + 6 negatives,
executed through the original harness code path once per shape:
**26/26 agree under P6, EXP, CHAL, and HYB alike.** Baseline:
the original harness on the file's own receipts re-ran here at
35/35. RFC 8785 gate: PASS (Appendix B 24/24 + 2/2, §3.2.3,
§3.2.4 hex-identical).

S01's 9 logical steps, receipts re-minted per shape, the file's
own expectations:

| Shape | Steps matched | The miss |
|---|---|---|
| P6 | 9/9 | — |
| EXP | 8/9 | step 2: the replay is ACCEPTED (inside the window) |
| CHAL | 9/9 | — (replay rejected: challenge consumed) |
| HYB | 9/9 | — |

W-series (predictions registered in DESIGN.md; every one held):

| Vector | Counts | Result |
|---|---|---|
| W01 in-window replay | replay inside validity | P6 reject, HYB reject, **EXP accept** |
| W02 post-window replay | window bounds replay | all reject (EXP/HYB on expiry, P6 on store) |
| W03 P6 state loss | durability dependence | wipe the store → P6 **accepts** the replay |
| W04 challenge replay | single-use | reject (consumed) |
| W05 challenge cross-context ×3 | binding | all reject (audience, binding, domain) |
| W06 HYB state loss + expiry | where the bound rescues | accept (in-window, state gone) / **reject at +301 s on expiry alone**; P6 control accepts at +301 s and at +30 days |
| W07 expiry boundary | exp exclusive | accept at exp−1, reject at exp |
| W08 clock skew ×2 | clock trust | reject both directions (future iat past leeway; early expiry) |
| W09 missing material ×6 | presence checks | all reject (no exp, no iat, HYB no exp, no/unknown/expired challenge) |
| W10 HYB pair keying | (signer, nonce) is the key | same nonce, other signer: accept |
| W11 CHAL restart | fail-closed | reject — availability cost, not a hole |
| W12 long-lived replay | intact store, +30 days | P6 reject, HYB reject |

## The deciding vectors

- **S01-step-2 / W01 decide EXP.** A receipt exists so that one
  presentation settles one claim. A shape that accepts the
  same receipt twice inside five minutes — with no state, by
  design — has traded the receipt's core property for
  operational simplicity. That is a worse standard for
  receipts, whatever it saves in storage.
- **W06 against its P6 control decides HYB over P6.** Same
  wipe, same receipt: HYB rejects the replay once the signed
  expiry has passed; P6 accepts it at +301 seconds and at
  +30 days, because nothing in a P6 receipt ever makes it
  stale. W03 shows the in-window half honestly: after a wipe,
  HYB accepts an in-window replay exactly as P6 does — the
  hybrid does not fix that, and this record does not claim
  it does. What it fixes is the unbounded half: under P6 a
  state loss re-opens every receipt ever accepted, forever;
  under HYB it re-opens only receipts still inside their
  window.
- **W11 + the round trip decide CHAL's tie.** CHAL matched
  P6 step for step, and its state is bounded by the challenge
  lifetime — a real elegance. But a relying party must issue
  before anyone can present, so a receipt stops being a
  single self-contained message (the thread's format, and
  the house's settled flow), and a restart rejects honest
  in-flight receipts (W11). It also leaves a residual no
  receipt-layer rule in any shape tested closes: a challenge
  is a bearer instrument inside its own context (DESIGN.md,
  W05's leaves-out). A tie on protection, a loss on shape.

## Honest costs of the winner (HYB)

- The durable pair-store is still required, unchanged, for
  everything inside a receipt's window. HYB is P6 plus a
  bound, not P6 minus the store.
- Clock trust enters: the RP's clock now decides early
  expiries and not-yet-valid rejections (W08). Both failure
  directions are fail-closed (reject), so the cost is
  availability, not safety — but a badly skewed RP refuses
  honest receipts.
- Two more signed fields (iat, exp), a 60-second leeway
  policy to state, and a pruning rule for the store (a pair
  may be forgotten once its receipt's exp has passed).
- Issuers must choose windows honestly: a window set to a
  century re-creates P6's unbounded hole inside HYB.

## The adoption note — does it stand?

**As written, yes.** The staged note
(`../hfq001-vectors-2026-11-14/adoption-note-STAGED.md`)
reports the owner's 2026-11-14 ruling, and the ruling was P6;
this comparison is DERIVED and adopts nothing. The note's
bytes are a true report of the standing ruling and need no
correction.

If the owner amends the adoption to the hybrid, exactly one
line changes — the second paragraph's first sentence. "Receipts
we issue carry the four fields — domain, audience, chain_id,
nonce." becomes: "Receipts we issue carry domain, audience,
chain_id and nonce, each receipt also bearing a signed
issued-at and expiry; a relying party may forget a recorded
pair once that expiry has passed, since after it the receipt
is refused on its face." Nothing else in the note moves: the
refusal sentence already describes the pair-store check, and
the closing paragraph (the wiring is the named next step) is
exactly where the amendment would land when built.

## What would prove this verdict wrong

- Any case where HYB accepts what P6 rejects. None exists in
  this suite; one would mean the added time checks can only
  subtract rejections somewhere I have not seen — e.g. an
  iat/exp spelling two honest verifiers parse to different
  instants, which would also be a new vector against the
  profile's string-spelled times.
- A showing that the house's real receipt flow needs
  long-lived presentations — a receipt legitimately presented
  months after issue. The suite models the thread's receipt
  shape, where presentation is prompt. If the house's flow
  is not prompt, the window is a real cost against HYB and
  the verdict re-opens.
- An independent implementation disagreeing with any cell of
  the table above.
- A challenge variant that binds the challenge to a named
  presenter (issued over an authenticated channel), closing
  CHAL's bearer residual — that would re-open the CHAL
  comparison, though the round-trip cost would remain.

## Lesson

The wider comparison's real yield is a map of where each
shape's protection physically lives: P6's lives in the
verifier's memory, EXP's in the signer's clock claims,
CHAL's in a conversation, HYB's in memory bounded by time.
"Better" turned out not to be a different mechanism but a
bound on the adopted one's known unbounded case — the
family's champion was beaten only by itself, plus an expiry.
Bottle-back: when a comparison is ordered against an adopted
profile, register the champion's own conceded weakness as a
vector first (here W03/W06) — the outside shapes earn their
keep by pricing that weakness, not by novelty.

## Files

- `DESIGN.md` — shapes, vector registration, predictions (8,424 B)
- `compare.py` — the harness (21,139 B)
- `results-run1.json` / `results-run2.json` — full per-case
  outcomes, byte-identical (51,580 B each)
- `run-log.txt` — the human-readable run log (8,243 B)
- `VERDICT.md` — this record
