# ClaimCheck — Web-Evidence Claim Registry

A standalone Intelligent Contract primitive that lets any builder register a
claim against a public web source and have it resolved by validator consensus,
instead of trusting whoever submitted or resolved it.

## Why this exists

DAOs, bounty platforms and prediction / attestation apps all run into the same
problem: "does this public page actually show X happened?" Today that is either
checked by a trusted person, or by a single oracle feed. ClaimCheck turns it
into a reusable on-chain primitive:

1. `submit_claim(statement, source_url, criteria)` — the claim is bound to one
   source and to explicit criteria at submission time. They cannot be swapped
   later to steer the result.
2. `resolve_claim(claim_id)` — anyone may trigger it, nobody picks the outcome.
   Validators independently fetch the bound source and judge the bound criteria.
3. The verdict is stored immutably. If the source page changes afterwards, the
   honest move is a new claim, not editing the old record.

## How consensus is used — two different equivalence checks, on purpose

This is the part most demos get wrong by using one check for everything.

| Output | Check | Why |
|---|---|---|
| Verdict: `SUPPORTED` / `CONTRADICTED` / `INSUFFICIENT` | `gl.eq_principle.strict_eq` | It is a closed enum. The prompt forces a one-word answer, the code normalises it, and validators must match exactly. Fuzzy agreement on a verdict would be a bug, not a feature. |
| Evidence: one-sentence summary | `gl.eq_principle.prompt_comparative` | Two honest validators will word a summary differently. Byte equality would reject good results, so validators compare factual meaning instead — same cited fact means equivalent. |

Non-deterministic blocks never touch storage. Statement, source and criteria
are copied into local variables first and only captured by the closures.

## State design

Separate `TreeMap[u256, str]` maps per field (statement, source, criteria,
status, evidence) plus a `claim_count` counter. Statuses form a one-way state
machine: `PENDING -> SUPPORTED | CONTRADICTED | INSUFFICIENT`. There is no
method that mutates a resolved claim.

## What it is not

Not a generic "ask the AI" wrapper: the LLM never sees a free-form question
from the resolver, only the statement / criteria / source fixed at submission,
and its verdict still has to survive strict validator equality.

## Try it in GenLayer Studio

1. Paste `contracts/claim_check.py` into Studio and deploy (no constructor args).
2. Call `submit_claim` with, for example:
   - statement: `The page announces a mainnet launch date for the project.`
   - source_url: an https announcement page you want checked
   - criteria: `Supported only if the page states a specific launch date.`
3. Call `resolve_claim(0)`, then `get_claim(0)`.

Expected behaviour: a page with no date resolves `INSUFFICIENT` rather than
being guessed into `SUPPORTED` — that third state is deliberate, so builders
can tell "false" apart from "not proven".

## Tests

See `tests/test_cases.md` for the direct-test scenarios covered: input
validation, unknown / double resolution, and the three verdict paths.
