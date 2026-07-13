"""
Dataset Retrieval Layer
========================
Where your state welfare-scheme datasets get searched from the DB.
Pipeline: User -> Frontend -> Django API -> [this module] -> Prompt Builder -> LLM Client
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

DATASET_DIR = Path(__file__).resolve().parent / "datasets"

# Confirmed against actual DB values (SELECT DISTINCT state FROM schemes_scheme).
STATE_KEY_TO_DB_VALUE = {
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
    "uttarakhand": "uttarakhand",
    "haryana": "haryana",
    "chandigarh": "chandigarh",
    "puducherry": "puducherry",
}

STATE_NAME_ALIASES = {
    "telangana": ["telangana"],
    "andhra_pradesh": ["andhra pradesh", "andhra"],
    "tamil_nadu": ["tamil nadu", "tamilnadu"],
    "karnataka": ["karnataka"],
    "kerala": ["kerala"],
    "uttar_pradesh": ["uttar pradesh"],
    "madhya_pradesh": ["madhya pradesh"],
    "bihar": ["bihar"],
    "rajasthan": ["rajasthan"],
    "maharashtra": ["maharashtra"],
    "uttarakhand": ["uttarakhand"],
    "haryana": ["haryana"],
    "chandigarh": ["chandigarh"],
    "puducherry": ["puducherry", "pondicherry"],
}


def detect_state(query: str) -> Optional[str]:
    q = query.lower()
    for state_key, aliases in STATE_NAME_ALIASES.items():
        if any(alias in q for alias in aliases):
            return state_key
    return None


PROMPT_FIELDS = ("name", "eligibility", "benefits", "how_to_apply", "state")


class SchemeDataset:
    @classmethod
    def load(cls, state: Optional[str] = None) -> List[Dict]:
        from schemes.models import Scheme
        from django.db.models import Q

        queryset = Scheme.objects.filter(is_active=True)
        if state:
            mapped_state = STATE_KEY_TO_DB_VALUE.get(state.lower(), state.lower())
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
        pass


class SchemeRetriever:
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
        query_terms = [t.strip(".,?!;:()\"'") for t in raw_terms]
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
        return [record for _, record in scored[:limit]]

    @staticmethod
    def to_context_lines(schemes: List[Dict]) -> List[str]:
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
