# HFQ-001 — Wider receipt-profile comparison — DESIGN (registered before any run)

Date: 2026-11-15. Ordered by the owner in the HF WORK chat
("Run the wider comparison"). Internal work only: $0, no outward
posts, the staged adoption note stays staged and unposted.
State of everything in this folder until a second witness exists:
DERIVED.

## The question

P6 was adopted 2026-11-14 on the strength of the thread's own
family (P0–P6 postures over one shared byte layer) and its 35
vectors, run 35/35 twice by our independent verifier
(`../hfq001-vectors-2026-11-14/`). That proof's scope is the
family. This run asks: does any shape OUTSIDE that family beat
P6 at the layer where P6 actually lives — the relying-party
layer (field binding + replay/freshness enforcement)?

## What is held constant (not under comparison)

All four shapes share the byte and signature layer exactly as
the 2026-11-14 run verified it: pair-preserving parse; P1
(duplicates after unescaping), P2 (lone surrogates, NFC), P3
(number-token magnitude ≤ 2^53−1 on the token), P4 (top-level
proof exclusion only), P5 (low-s), P7 (framing pinned per signer
from the discovery document, no fallback); JCS canonical bytes;
SHA-256; EIP-191 recovery under both framings. The original 35
outcomes therefore run against every shape: the 20 vectors and
6 negatives execute through the original harness code path
unchanged, once per shape, and the 9 S01 steps run as the same
logical steps against receipts re-minted per shape (the file's
S01 receipts are P6-format receipts; running them byte-identical
under a differently formatted profile would test the format
difference, not the enforcement difference — the steps, signers,
field mutations, and order are unchanged).

## The four shapes, defined precisely

Common relying-party (RP) configuration, from the vector file:
domain `covenant-earn-receipt/v1`, audience (me) `aemb.pro`,
chain_id `eip155:8453`. Every shape first requires: valid
signature(s) recovering to a discovery-document signer under
its pinned framing, low-s; profile fault = reject. Field checks
(a)–(c) are common to all shapes: domain must equal the RP's
expected domain (missing counts as unequal), audience must
equal the RP itself, chain_id must equal the RP's required
chain. Shapes differ only in the freshness/replay clause (d).

- **P6 (champion, as adopted).** Receipt carries domain,
  audience, chain_id, nonce. Clause (d): nonce must be present;
  the RP keeps a durable store of accepted (signer, nonce)
  pairs; a pair already in the store is rejected; on acceptance
  the pair is recorded (check-and-record atomic and durable —
  the harness models the store as a set; durability failure is
  tested explicitly by W03/W06, it is not assumed). No time
  field is consulted; a receipt never expires.
- **EXP (stateless signed-expiry).** Receipt carries domain,
  audience, chain_id, nonce, plus signed `iat` and `exp`
  (RFC 3339 UTC strings, same spelling as the file's `t`).
  Clause (d): nonce, iat, exp must all be present; reject if
  iat > now + 60 s (clock-skew leeway) or now ≥ exp. The RP
  keeps NO store of any kind. Test mints use exp − iat = 300 s.
- **CHAL (challenge-bound).** Before presentation, the RP
  issues a challenge: an id bound to (domain, audience,
  chain_id, expiry) chosen by the RP; challenge lifetime 120 s
  in test mints. The receipt carries domain, audience,
  chain_id, nonce, and `chal` (the challenge id), all signed.
  Clause (d): nonce and chal present; chal must name a
  challenge the RP issued, not yet expired, not yet consumed,
  whose bound (domain, audience, chain_id) equal the receipt's
  own fields; on acceptance the challenge is consumed. RP state
  is the issued-challenge table only; entries are worthless
  after their expiry, so state is bounded by lifetime, and a
  restart loses outstanding challenges (fail-closed; tested by
  W11). The challenge id is delivered to the presenter out of
  band; the harness models issuance as an explicit step.
- **HYB (hybrid: P6 + signed expiry bound).** Exactly P6, plus
  signed `iat` and `exp` with EXP's time checks (leeway 60 s,
  test window 300 s). The (signer, nonce) store is still kept,
  but a pair may be pruned once the receipt's exp has passed;
  after pruning, a replay of that receipt is still rejected —
  on expiry. Within the window, HYB's replay behaviour is
  P6's, including its dependence on the store (tested by W06).

Considered and not swapped in: EIP-712 typed-data domain
separation. It binds domain and chain_id into the signature
digest structurally — a hardening of clauses (a)/(c) at the
signature layer — but it carries no audience or replay rule,
so it does not compete with clause (d), where every difference
in this comparison lives. It could combine with any shape
here; the thread already named it the clean route and it stays
open independently of this verdict.

## New vectors, registered before running (W-series)

Times are simulated. T0 = 2026-11-15T12:00:00Z. "Present"
means: run the shape's full verifier (byte layer + signature +
field checks + clause (d)) at the stated simulated now, against
the stated RP state. Predictions are registered here so the
run tests them, not just the shapes.

- **W01 — in-window replay, EXP focus.** Mint EXP receipt R
  (iat T0, exp T0+300). Present at T0+10, present again at
  T0+20. Counts: whether the shape stops a replay inside the
  validity window. Leaves out: replay after the window (W02).
  Predictions: EXP accept/accept (the shape's known price);
  P6 reject on second (store); HYB reject on second (store);
  CHAL n/a (its replay case is W04).
- **W02 — post-window replay, EXP.** Same R presented at
  T0+10, then at T0+301. Counts: whether the window bounds
  replay at all. Predictions: EXP reject (expired); P6/HYB
  reject (store — P6 has no window; the rejection cause
  differs and is recorded).
- **W03 — verifier state loss, P6.** Accept R under P6; wipe
  the store (restart); present R again. Counts: P6's total
  dependence on durable state — the exact property P6d's own
  text demands ("atomic and durable") and the original file
  concedes its vectors cannot test. Predictions: P6 accepts
  the replay (the clause's protection is gone with the
  state). Leaves out: whether production could make a wipe
  impossible — an operational claim no harness settles.
- **W04 — challenge replay, CHAL.** Issue challenge; present
  R answering it (accept); present R again with the same
  challenge. Counts: challenge single-use. Prediction: reject
  (consumed).
- **W05 — challenge carried across audience/domain, CHAL.**
  (i) Challenge bound to audience `other.example`; receipt
  with audience `other.example` presented to the RP (me =
  aemb.pro): prediction reject (audience ≠ me). (ii) Same
  challenge; receipt audience field set to `aemb.pro` while
  the challenge binds `other.example`: prediction reject
  (binding mismatch). (iii) Challenge bound to a different
  domain, receipt domain matching the RP: prediction reject
  (binding mismatch). Counts: whether a challenge minted for
  one context can be spent in another. Leaves out: theft of
  an unconsumed challenge inside its own context (that is
  W04's complement and a real residual: whoever holds the
  challenge can spend it once — recorded as a cost, not
  tested as a vector, because no receipt-layer rule in any
  shape binds a challenge to a presenter).
- **W06 — state loss + expiry, HYB vs P6.** Accept R (HYB:
  iat T0, exp T0+300) at T0+10; wipe the store; present at
  T0+20; present at T0+301. Counts: exactly where the expiry
  bound rescues state loss and where it does not.
  Predictions: HYB accepts at T0+20 (within window, state
  gone — the hybrid does NOT fix in-window state loss) and
  rejects at T0+301 (expired, state or no state). P6 control,
  same wipe, present at T0+301 and at T0+30 days: accepts
  both (no expiry exists to reject on).
- **W07 — expiry boundary, EXP and HYB.** R with exp =
  T0+300 presented at now = T0+299 and at now = T0+300.
  Counts: boundary semantics (exp is exclusive). Predictions:
  accept, then reject.
- **W08 — clock skew, EXP (HYB inherits).** (i) R with iat
  T0 presented to an RP whose clock reads T0−120: iat sits
  120 s in the RP's future, past the 60 s leeway — prediction
  reject (not yet valid). (ii) Same R presented to an RP whose clock reads
  T0+330: its exp (T0+300) sits 30 s in the RP's past
  though the receipt itself is fresh — prediction reject
  (early expiry). Counts: clock trust — whether a skewed
  RP fails closed in both directions. It does: both
  directions reject, so a bad clock costs availability,
  not safety.
- **W09 — missing freshness material.** (a) EXP receipt
  with `exp` removed, presented at T0+10: prediction
  reject (clause (d) requires exp present). (b) EXP
  receipt with `iat` removed: prediction reject. (c) HYB
  receipt with `exp` removed: prediction reject. (d)
  CHAL receipt carrying no `chal`: prediction reject.
  (e) CHAL receipt naming a challenge this RP never
  issued: prediction reject. (f) CHAL receipt answering
  a challenge issued at T0, presented at T0+121 — past
  the challenge's 120 s lifetime: prediction reject.
  Counts: whether clause (d)'s presence checks are
  real — a missing or dead field must reject, not pass
  as an unchecked field.
- **W10 — pair keying, HYB.** Present R (signer A, nonce
  N) at T0+10; then present a receipt carrying the same
  nonce N from a different signer at T0+20. Counts:
  whether the store's key is the (signer, nonce) pair
  or the nonce alone — a nonce-only key would reject
  the second presentation and let one signer squat a
  nonce against every other signer. Prediction:
  accept/accept (the key is the pair).
- **W11 — challenge restart, CHAL.** Issue a challenge
  at T0+10; mint R answering it; restart the RP (the
  issued-challenge table is lost); present R at T0+20.
  Counts: whether CHAL fails closed when its state is
  lost — the mirror of W03, where P6's lost state opens
  the door. Prediction: reject (the challenge is
  unknown to the restarted RP) — an availability cost,
  not a hole: honest in-flight receipts are refused
  until a fresh challenge is issued.
- **W12 — long-lived replay, store intact, P6 and HYB.**
  Accept R at T0+10; present R again at T0+30 days,
  the store intact throughout. Counts: the store's
  memory over long horizons — the complement of W03
  and W06, where the store is wiped. Predictions:
  accept, then reject, under both shapes (under P6 on
  the recorded pair; under HYB on the recorded pair,
  or, if the pair was pruned after expiry, on expiry).
