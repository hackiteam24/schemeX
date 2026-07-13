"""
Prompt Builder
==============
Assembles the final message list sent to the LLM client. Kept separate from
views.py so the system prompt, language handling, user-profile grounding,
and retrieved-scheme context can evolve independently of request handling —
and so it works identically no matter which provider get_llm_client() returns.

Today `retrieved_schemes` will always be [] (see retrieval.py — no dataset
files exist yet), so build_system_prompt() produces exactly what views.py
was already sending. Once datasets land, grounding context is appended
automatically — no changes needed here or in views.py.
"""

from typing import Dict, Iterable, List, Optional

from .retrieval import SchemeRetriever

SYSTEM_PROMPT = (
    SYSTEM_PROMPT
) = """You are SchemeX AI, a friendly multilingual assistant that helps rural and \
semi-urban Indian citizens discover government welfare schemes, check eligibility, understand \
application processes, and know required documents. Only state specific scheme names, amounts, \
and eligibility details that appear in the verified scheme data provided to you — never invent or \
guess scheme names, benefit amounts, or eligibility rules. If no verified data is provided for the \
user's question, say you don't have confirmed details on that and suggest checking the official \
scheme portal or nearest Gram Panchayat/CSC, rather than answering from general knowledge. Keep \
answers short, simple, and in plain language (avoid jargon since many users may not be highly \
literate). If asked something outside government schemes, politely redirect back to how you can \
help with scheme discovery."""

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
}

# Hard ceiling on how many prior turns get replayed to the model. Keeps token
# usage bounded as conversations grow long, regardless of provider/pricing.
MAX_HISTORY_MESSAGES = 10


def build_system_prompt(
    language: str,
    retrieved_schemes: Optional[List[Dict]] = None,
    user_context: str = "",
) -> str:
    """
    Builds the system prompt: base instructions + language directive +
    optional user-profile context + optional retrieved-scheme grounding.
    """
    lang_name = LANGUAGE_NAMES.get(language, "English")

    prompt = (
        SYSTEM_PROMPT
        + f"\n\nRespond ONLY in {lang_name}, regardless of what language the user's question is written in."
    )

    if user_context:
        prompt += "\n\n" + user_context

   if retrieved_schemes:
        lines = SchemeRetriever.to_context_lines(retrieved_schemes)
        listing_instruction = (
            "\n\nIf there are more than 3 schemes below, list ALL of them as a short bulleted list "
            "(just the scheme name + one-line benefit each) rather than deep-diving into only one. "
            "Only give full eligibility/benefit/application detail for a specific scheme if the user "
            "names it or asks about just one."
            if len(retrieved_schemes) > 3 else ""
        )
        prompt += (
            "\n\nUse the following verified scheme data as your primary source of truth for this "
            "reply. Prefer it over your own general knowledge, and don't invent details it doesn't contain:"
            + listing_instruction + "\n"
            + "\n".join(f"- {line}" for line in lines)
        )
    else:
        prompt += (
            "\n\nNo verified scheme data matched this message. Do not name specific schemes or "
            "amounts from memory — ask a clarifying question (e.g. which state, which category) "
            "or suggest the official scheme portal instead."
        )
    return prompt 

def build_messages(
    language: str,
    history: Iterable,
    retrieved_schemes: Optional[List[Dict]] = None,
    user_context: str = "",
) -> List[Dict]:
    """
    Builds the full messages array (system + conversation history) ready to
    send to any LLM client from llm_client.py.

    `history` should already be capped and in chronological order (oldest
    first) — see views.py, which fetches the most recent MAX_HISTORY_MESSAGES
    turns and reverses them before calling this.
    """
    messages = [
        {
            "role": "system",
            "content": build_system_prompt(language, retrieved_schemes, user_context),
        }
    ]

    for m in history:
        messages.append(
            {
                "role": "user" if m.sender == "user" else "assistant",
                "content": m.content,
            }
        )

    return messages
