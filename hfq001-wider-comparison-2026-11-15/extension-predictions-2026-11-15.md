# HFQ-001 — Wider comparison — EXTENSION predictions (registered before any run)

Registered: 2026-11-15T21:39Z (15:39 CST), before the
extension harness was written or run. These two cells were
proposed by Lawless1987 in topic 180706, post #26
(2026-11-15T18:37Z), in his words below. Everything else —
definitions, shapes, predictions, mechanism reasoning — is
ours, fixed here so the run tests them.

His proposals, verbatim in substance:

1. "After a pair is pruned, a new receipt from the same
   signer that reuses that nonce, with a fresh iat and exp,
   passes HYB. P6 refuses it, because P6 keeps every pair.
   Whether that matters depends on whether a nonce is meant
   to be unique forever or only within a window. The profile
   should say which, and it would make a good W vector
   either way."
2. "The relying party could check that instead of trusting
   it: refuse any receipt whose exp − iat exceeds a maximum
   it publishes. Together with your existing check on an
   iat in the future, that bounds how long a pair must be
   stored and how long a replay stays open after a loss, by
   a number the relying party chose. It doesn't bound how
   many pairs are stored. That is another W vector: a
   window over the cap is rejected."

Held constant: everything DESIGN.md holds constant — the
shared byte/signature layer, the RP configuration (domain
`covenant-earn-receipt/v1`, audience `aemb.pro`, chain_id
`eip155:8453`), T0 = 2026-11-15T12:00:00Z, leeway 60 s,
standard test window 300 s, simulated time. The extension
harness imports compare.py's verifier, minting, and RP code
unchanged and adds only the two mechanisms under test
(pruning exercised; a cap check inside clause (d)'s time
checks). State changes only on accept, as in compare.py.

## X1 — post-pruning nonce reuse

Definition. One signer (A), one nonce N throughout.

- HYB, pruning exercised: mint R1 (iat T0, exp T0+300).
  Present R1 at T0+10. Advance the clock to T0+301 and
  prune: drop every recorded pair whose receipt's exp has
  passed (DESIGN.md licenses exactly this: "a pair may be
  pruned once the receipt's exp has passed"). Mint R2 — a
  NEW receipt, same signer, same nonce N, fresh iat T0+400
  and exp T0+700. Present R2 at T0+410. Then present R1
  again at T0+410.
- HYB, unpruned control: identical, except no pruning step
  is ever taken (the pair is kept past its exp). Present
  R1 at T0+10, R2 at T0+410.
- P6 control: R1 carries no time fields (P6 has none).
  Present R1 at T0+10. No pruning exists to take. Mint R2 —
  new receipt, same signer, same nonce N — and present it
  at T0+410.

Shapes run, and why only these: the vector discriminates
exactly the shapes that keep a (signer, nonce) pair-store —
HYB (which prunes) against P6 (which never prunes). EXP
keeps no store and CHAL's single-use mechanism is the
challenge, not the nonce; in both, "after a pair is pruned"
has no referent and a fresh receipt's acceptance is true by
construction, not a finding. W10 already settled the other
keying question (the key is the pair, not the nonce alone);
X1 holds the signer fixed, as his case does.

Predictions:

- HYB, pruned: **accept / accept / reject.** R1 accepted
  and recorded. After pruning, the store holds no pair for
  (A, N); R2's own window is fresh and valid, its signature
  and fields check, and nothing else in clause (d) keys on
  nonce history — so R2 is accepted. R1 presented again is
  rejected on expiry (now ≥ its exp): pruning frees the
  nonce, it does not revive the old receipt.
- HYB, unpruned control: **accept / reject.** Same receipts,
  same times; the only difference is the kept pair, so a
  reject here isolates pruning as the cause of the pruned
  arm's second accept.
- P6: **accept / reject.** P6 keeps every pair and has no
  time field that could license forgetting one; the pair
  recorded at T0+10 is still in the store when R2 arrives.

What it settles: whether HYB as defined in DESIGN.md in
fact accepts a post-pruning nonce reuse that P6 refuses —
the one case he named where HYB accepts what P6 rejects.
It does not settle whether the profile SHOULD free a nonce
after its window; that is the profile-text question he
named (unique forever, or unique within a window), and the
cell's job is to make the current text's answer observable.

Falsifier: any outcome differing from the three sequences
above — e.g. the pruned HYB arm rejecting R2 (some other
rule is carrying nonce history), or P6 accepting R2 (the
store is not doing what the profile says).

## X2 — RP-enforced exp − iat cap

Definition. The RP publishes a maximum window CAP = 300 s
(the comparison's standard test window, so every receipt
minted anywhere in the original suite sits exactly at the
cap). Clause (d)'s time checks gain one rule, evaluated
with them: reject if exp − iat > CAP, with the cap named
as the rejection cause. "Exceeds" is strict: a window of
exactly CAP does not exceed it.

- X2a, at the cap: standard receipt (iat T0, exp T0+300),
  presented at T0+10.
- X2b, one second over: iat T0, exp T0+301, presented at
  T0+10 (inside its window; only the cap can reject it).
- X2c, the dishonest window: iat T0, exp T0+30 days,
  presented at T0+10 (the "window set to a century" cost
  from VERDICT.md, scaled to 30 days).
- X2d, no existing cell moves: the original suite's EXP
  and HYB cells — W01, W02, W06 (HYB), W07, W08(i)/(ii),
  W09a, W09b, W09c, W12 (HYB) — re-run against the capped
  RP, outcomes compared cell by cell with the uncapped
  run in results-run1.json.

Shapes run, and why only these: EXP and HYB are the two
shapes whose receipts carry signed iat/exp. P6 and CHAL
receipts carry no time fields, so a window cap has nothing
to evaluate; extending their formats to carry iat/exp
would test a new format, not this rule.

Predictions:

- X2a: **accept** under both EXP and HYB (300 does not
  exceed 300; all other checks are the standard ones).
- X2b: **reject** under both, cause = the cap. Under HYB
  the pair must NOT be recorded (state changes only on
  accept), so the same receipt's rejection leaves the
  store untouched.
- X2c: **reject** under both, cause = the cap.
- X2d: **every re-run cell identical to the uncapped
  run.** Every mint in the original suite uses
  exp − iat = 300 = CAP, so the cap rule never fires
  there; a cap set at the standard window is purely
  additive — it rejects only windows no honest mint in
  the suite ever used.

What it settles: whether an RP-side cap rejects an
over-wide window on the RP's own number (his vector), and
whether adopting the cap at the standard window disturbs
any settled cell. It does not settle his own stated limit:
the cap bounds how long a pair must be stored and how
long a replay stays open after a loss; it does not bound
how many pairs are stored.

Falsifier: X2a rejecting (the cap as defined is not the
cap as implemented), X2b or X2c accepting under either
shape, or any X2d cell differing from results-run1.json.

## Run discipline

The extension runs each cell twice; the two runs' outcomes
must agree exactly. Predictions above were written before
compare-extension.py existed. A prediction that misses is
reported as a finding, not edited away.
