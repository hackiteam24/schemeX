"""
Dataset Retrieval Layer
========================
Where your state welfare-scheme datasets (Andhra Pradesh, Telangana, Tamil
Nadu, Karnataka, ...) plug in. Today this returns [] — no data files exist
yet — so nothing downstream changes behavior. Drop JSON files into
DATASET_DIR (see STATE_DATASET_FILES below) and it starts grounding answers
immediately, no other code changes needed.

Pipeline:
    User -> Frontend -> Django API -> [this module] -> Prompt Builder -> LLM Client -> AI Response

Expected on-disk layout (create this folder when you add real data):
    backend/chatbots/datasets/
        andhra_pradesh.json
        telangana.json
        tamil_nadu.json
        karnataka.json

Each file: a list of scheme records. Keep records lean — every extra field
is extra tokens sent to the model on every relevant query:
    [
      {
        "id": "ap-001",
        "name": "...",
        "state": "andhra_pradesh",
        "category": "agriculture",
        "eligibility": "...",
        "benefits": "...",
        "how_to_apply": "..."
      }
    ]
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

DATASET_DIR = Path(__file__).resolve().parent / "datasets"

# Add one entry here per state dataset file as they arrive.
STATE_DATASET_FILES = {
    "central": "central.json",
    "andhra_pradesh": "andhra_pradesh.json",
    "telangana": "telangana.json",
    "tamil_nadu": "tamil_nadu.json",
    "karnataka": "karnataka.json",
}

# Only these fields ever get sent to the model. Datasets can carry extra
# metadata (source URLs, last-verified dates, internal IDs) without that
# bloating every prompt — trim what actually reaches the LLM here, in one place.
PROMPT_FIELDS = ("name", "eligibility", "benefits", "how_to_apply", "state")


class SchemeDataset:
    """
    Loads active scheme records from the database.
    """

    @classmethod
    def load(cls, state: Optional[str] = None) -> List[Dict]:
        from schemes.models import Scheme
        from django.db.models import Q

        queryset = Scheme.objects.filter(is_active=True)
        if state:
            state_mapping = {
                "central": "all",
                "andhra_pradesh": "andhra",
                "telangana": "telangana",
                "tamil_nadu": "tamilnadu",
                "karnataka": "karnataka",
                "kerala": "kerala",
                "uttar_pradesh": "up",
                "madhya_pradesh": "mp",
                "bihar": "bihar",
                "rajasthan": "rajasthan",
                "maharashtra": "maharashtra",
            }
            mapped_state = state_mapping.get(state.lower(), state.lower())
            queryset = queryset.filter(Q(state__iexact=mapped_state) | Q(state__iexact="all"))

        records = []
        for s in queryset:
            records.append({
                "id": str(s.id),
                "name": s.name,
                "state": s.state,
                "category": s.category,
                "eligibility": s.eligibility_criteria,
                "benefits": s.benefits,
                "how_to_apply": s.how_to_apply
            })
        return records

    @classmethod
    def clear_cache(cls):
        """No-op since we load from database now."""
        pass


class SchemeRetriever:
    """
    Relevant Scheme Search layer. Given a user's query (+ optional state),
    returns the most relevant scheme records to ground the AI's answer in
    real data instead of relying only on the model's pretrained knowledge.

    Today: naive keyword-overlap scoring (fine for launch — swap for
    embeddings/vector search later without touching any caller of this class,
    since the public interface — search() returning a list of dicts — stays
    the same either way).
    """

    # Common words that would otherwise false-match almost every record and
    # waste both retrieval precision and prompt tokens on irrelevant schemes.
    _STOPWORDS = {
        "a", "an", "the", "is", "are", "am", "i", "my", "me", "for", "of", "to",
        "in", "on", "and", "or", "any", "there", "this", "that", "do", "does",
        "can", "will", "it", "its", "be", "with", "if", "you", "your", "how",
        "what", "please",
    }

    def search(self, query: str, state: Optional[str] = None, limit: int = 3) -> List[Dict]:
        records = SchemeDataset.load(state)
        if not records or not query:
            return []

        raw_terms = query.lower().strip(".,?!;:()\"'").split()
        query_terms = [
            t.strip(".,?!;:()\"'")
            for t in raw_terms
        ]
        query_terms = [t for t in query_terms if t and t not in self._STOPWORDS and len(t) > 2]

        if not query_terms:
            return []

        scored = []

        for record in records:
            haystack = " ".join(str(record.get(f, "")) for f in PROMPT_FIELDS).lower()
            score = sum(haystack.count(term) for term in query_terms)
            if score > 0:
                scored.append((score, record))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        # Small limit (default 3) is deliberate: each matched scheme costs
        # prompt tokens on every request. Raise it only if answer quality
        # actually needs more context, not "just in case."
        return [record for _, record in scored[:limit]]

    @staticmethod
    def to_context_lines(schemes: List[Dict]) -> List[str]:
        """
        Token-frugal formatting: one compact line per scheme with only the
        fields the model needs to answer (name/eligibility/benefits/how to
        apply) — never a raw dict dump, which wastes tokens on punctuation,
        internal IDs, and keys the model doesn't need repeated back to it.
        """
        lines = []
        for s in schemes:
            parts = [s.get("name", "Unknown scheme")]
            if s.get("eligibility"):
                parts.append(f"Eligibility: {s['eligibility']}")
            if s.get("benefits"):
                parts.append(f"Benefits: {s['benefits']}")
            if s.get("how_to_apply"):
                parts.append(f"How to apply: {s['how_to_apply']}")
            lines.append(" | ".join(parts))
        return lines