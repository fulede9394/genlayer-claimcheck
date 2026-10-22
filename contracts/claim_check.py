# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing


class ClaimCheck(gl.Contract):
    """
    ClaimCheck - a reusable web-evidence claim registry primitive.

    A claim is bound at submission time to:
      1. a statement (what is being claimed)
      2. a source URL (the only evidence source a resolver may use)
      3. criteria (what counts as supporting the statement)

    Anyone may trigger resolution, but nobody chooses the outcome.
    Validators independently fetch the same source and judge the
    same criteria, so the caller cannot steer the verdict.
    Resolved claims are immutable. If a source changes, submit a
    new claim instead of rewriting history.
    """

    claim_count: u256
    statements: TreeMap[u256, str]
    sources: TreeMap[u256, str]
    criteria_map: TreeMap[u256, str]
    statuses: TreeMap[u256, str]
    evidences: TreeMap[u256, str]

    PENDING = "PENDING"
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT = "INSUFFICIENT"

    def __init__(self):
        self.claim_count = u256(0)

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------
    @gl.public.write
    def submit_claim(self, statement: str, source_url: str, criteria: str) -> int:
        statement = statement.strip()
        source_url = source_url.strip()
        criteria = criteria.strip()

        assert len(statement) >= 10, "statement too short"
        assert len(statement) <= 500, "statement too long"
        assert source_url.startswith("https://"), "source must be an https URL"
        assert len(source_url) <= 300, "source URL too long"
        assert len(criteria) >= 10, "criteria too short: say what counts as support"
        assert len(criteria) <= 500, "criteria too long"

        claim_id = self.claim_count
        self.statements[claim_id] = statement
        self.sources[claim_id] = source_url
        self.criteria_map[claim_id] = criteria
        self.statuses[claim_id] = self.PENDING
        self.evidences[claim_id] = ""
        self.claim_count = claim_id + u256(1)
        return int(claim_id)

    @gl.public.write
    def resolve_claim(self, claim_id: int) -> str:
        cid = u256(claim_id)
        assert cid in self.statuses, "unknown claim"
        assert self.statuses[cid] == self.PENDING, "claim already resolved"

        # Copy storage into locals: non-deterministic blocks may not
        # touch contract storage, they may only capture local values.
        statement = self.statements[cid]
        source_url = self.sources[cid]
        criteria = self.criteria_map[cid]

        # --- Step 1: verdict, checked with strict equality -----------
        # The verdict is a small closed set, so wording must not be
        # negotiated. We force the model to answer with one enum word,
        # normalise it in code, and require validators to match exactly.
        def get_verdict() -> str:
            page = gl.nondet.web.render(source_url, mode="text")
            prompt = f"""Judge one claim using only the page below.

Claim: {statement}
Criteria for support: {criteria}

Page content:
{page[:4000]}

Reply with exactly one word, nothing else:
SUPPORTED - the page clearly meets the criteria
CONTRADICTED - the page clearly shows the claim is false
INSUFFICIENT - the page does not contain enough information"""
            raw = gl.nondet.exec_prompt(prompt).strip().upper()
            if "CONTRADICTED" in raw:
                return "CONTRADICTED"
            if "SUPPORTED" in raw:
                return "SUPPORTED"
            return "INSUFFICIENT"

        verdict = gl.eq_principle.strict_eq(get_verdict)

        # --- Step 2: evidence summary, checked comparatively --------
        # A one-sentence summary will never be byte-identical across
        # validators, and that is fine. What must match is the factual
        # meaning, so this step uses comparative equivalence instead.
        def get_evidence() -> str:
            page = gl.nondet.web.render(source_url, mode="text")
            prompt = f"""In one short sentence, state the key evidence on
this page about the claim below. Quote the relevant fact or figure
if there is one. Do not add information that is not on the page.

Claim: {statement}
Page content:
{page[:4000]}"""
            return gl.nondet.exec_prompt(prompt).strip()[:280]

        evidence = gl.eq_principle.prompt_comparative(
            get_evidence,
            task="Summarise, in one short sentence, the key evidence "
                 "on the source page about this claim. Two summaries "
                 "are equivalent if they cite the same fact.",
        )

        self.statuses[cid] = verdict
        self.evidences[cid] = evidence
        return verdict

    # ------------------------------------------------------------------
    # View methods
    # ------------------------------------------------------------------
    @gl.public.view
    def get_claim(self, claim_id: int) -> typing.Any:
        cid = u256(claim_id)
        assert cid in self.statuses, "unknown claim"
        return {
            "id": claim_id,
            "statement": self.statements[cid],
            "source_url": self.sources[cid],
            "criteria": self.criteria_map[cid],
            "status": self.statuses[cid],
            "evidence": self.evidences[cid],
        }

    @gl.public.view
    def get_status(self, claim_id: int) -> str:
        cid = u256(claim_id)
        assert cid in self.statuses, "unknown claim"
        return self.statuses[cid]

    @gl.public.view
    def get_claim_count(self) -> int:
        return int(self.claim_count)
