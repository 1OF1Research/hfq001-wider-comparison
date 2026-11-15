# Receipt profiles, compared wider

A re-runnable comparison of four relying-party shapes for signed
receipts, run against the receipt interop vectors published in
Hugging Face discuss topic 180706 (the covenant receipt vectors,
P1–P7) plus twelve new vectors aimed at what that suite never
tested: what happens when the verifier's own state is lost.

The four shapes share one byte and signature layer and differ
only in the relying party's rule:

- **P6** — the profile the thread's vectors define: signed
  domain, audience, chain_id and nonce; the relying party
  records each accepted (signer, nonce) pair and refuses a
  repeat.
- **EXP** — stateless signed expiry instead of a pair store.
- **CHAL** — the relying party issues a short-lived challenge
  the receipt must answer.
- **HYB** — P6 plus a signed issued-at and expiry, so a recorded
  pair may be forgotten once its receipt's expiry has passed.

## Re-run it

```
git clone https://github.com/1OF1Research/hfq001-wider-comparison
cd hfq001-wider-comparison/hfq001-wider-comparison-2026-11-15
python3 compare.py my-results.json
diff my-results.json results-run1.json
```

No output from `diff` means your run agrees with ours, cell for
cell. The two recorded runs (`results-run1.json`,
`results-run2.json`) are byte-identical to each other. The
sibling folder `hfq001-vectors-2026-11-14/` carries the shared
byte layer (`verify.py`, `jcs.py`) and the thread's vector file
(`source-vectors.json`), imported unchanged — the comparison
adds the four verifiers and the new vectors, nothing else.
Python 3, standard library only.

## The verdict, in three lines

The hybrid wins, narrowly, in exactly one place: after the
verifier's pair store is lost, a P6 receipt can be replayed at
any age — measured accepted at +30 days — because no P6 receipt
ever goes stale; the hybrid refuses the same replay once its
signed expiry has passed. The stateless shape accepts a replay
inside its own window and is out. The challenge shape matches
P6 on protection and loses on shape: a receipt stops being one
self-contained message. Full reasoning: `VERDICT.md`; the
design and the predictions registered before the run:
`DESIGN.md`.

## The honest limit

Inside its window, after a store loss, the hybrid is exactly as
open as P6 — the bound closes the unbounded half of the hole,
not the whole hole. And this is one harness from one author:
an independent re-run that disagrees with any cell is the
finding that matters, and this repo exists so anyone can
produce it.
