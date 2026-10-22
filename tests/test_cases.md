# Test cases (run in GenLayer Studio / direct tests)

## Deterministic — no web or LLM needed
1. Submit a valid claim -> returns id 0, `get_claim_count()` is 1, status PENDING.
2. Submit with an `http://` (not https) source -> rejected.
3. Submit with statement or criteria shorter than 10 chars -> rejected.
4. `get_claim(99)` on an unknown id -> rejected.
5. Resolve the same claim twice -> second call rejected ("already resolved").

## Non-deterministic — verdict paths
6. Source page clearly meets the criteria -> SUPPORTED, evidence cites the fact.
7. Source page clearly contradicts the statement -> CONTRADICTED.
8. Source page is real but says nothing about the claim -> INSUFFICIENT
   (must not be forced into SUPPORTED / CONTRADICTED).
9. Evidence wording differs between validators but cites the same fact
   -> still finalises (comparative equivalence), while a different verdict
   word from a validator does not pass strict equality.
