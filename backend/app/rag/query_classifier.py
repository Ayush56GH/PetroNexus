"""
PetroNexus Query Classification Engine (SIH 26121 Section 32 & CLAUDE.md Section 20)
Classifies user queries to prevent unnecessary database/telemetry retrieval dumps
and ensure natural AI assistant conversational behavior.
"""
import re
from typing import Dict, Any, List, Optional

class QueryClassifier:

    GENERAL_PATTERNS = [
        r"^what\s+is\s+azure\b",
        r"^what\s+is\s+python\b",
        r"^what\s+is\s+the\s+capital\b",
        r"^capital\s+of\b",
        r"^explain\s+machine\s+learning\b",
        r"^tell\s+me\s+a\s+joke\b",
        r"^who\s+is\b",
        r"^hello\b|^hi\b|^hey\b",
        r"^how\s+are\s+you\b",
        r"^what\s+is\s+cloud\s+computing\b",
        r"^what\s+is\s+ai\b",
        r"^what\s+is\s+chatgpt\b"
    ]

    PRODUCT_PATTERNS = [
        r"petronexus",
        r"sih\s*26121",
        r"ertmac",
        r"witsml",
        r"how\s+does\s+the\s+platform\s+work",
        r"what\s+features\s+does"
    ]

    ACTIVE_WELL_PATTERNS = [
        r"current\s+depth",
        r"active\s+well",
        r"bit\s+depth",
        r"current\s+formation",
        r"current\s+telemetry",
        r"what\s+is\s+the\s+depth",
        r"current\s+parameters",
        r"current\s+rop",
        r"current\s+torque",
        r"current\s+wob"
    ]

    LOOKAHEAD_PATTERNS = [
        r"ahead\s+of",
        r"look[\-\s]?ahead",
        r"upcoming\s+hazards?",
        r"next\s+\d+\s*m",
        r"what\s+is\s+ahead",
        r"approaching\s+formation",
        r"hazards?\s+ahead"
    ]

    DOCUMENT_PATTERNS = [
        r"show\s+(?:me\s+)?the\s+source",
        r"citation",
        r"page\s+number",
        r"wcr",
        r"ddr",
        r"daily\s+drilling\s+report",
        r"which\s+document",
        r"view\s+document"
    ]

    FOLLOW_UP_PATTERNS = [
        r"^why\s+(?:was\s+it|is\s+it|did\s+you)\s+flag",
        r"^why\s+did\s+i\s+receive\s+this\s+alert",
        r"^explain\s+this\s+alert",
        r"^which\s+(?:nearby|offset)\s+well\s+experienced\s+that",
        r"^tell\s+me\s+more\s+about\s+it",
        r"^what\s+happened\s+ahead\s+of\s+it\??$"
    ]

    DRILLING_KEYWORDS = [
        "mud loss", "lost circulation", "kick", "stuck pipe", "torque", "drag",
        "barail", "tipam", "formation", "drill", "well", "offset", "casing",
        "cement", "bha", "bit", "rop", "wob", "rpm", "ecd", "spp", "pit volume",
        "overpressure", "pore pressure", "pack-off", "dogleg", "tvd", "tvdss"
    ]

    @classmethod
    def classify(cls, query: str, conversation_context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Classifies incoming query into one of:
        - GENERAL
        - PETRONEXUS_PRODUCT
        - ACTIVE_WELL_ANALYSIS
        - LOOKAHEAD
        - DOCUMENT_SEARCH
        - FOLLOW_UP_TO_CURRENT_TOPIC
        - DRILLING_ENGINEERING
        - HISTORICAL_WELL_KNOWLEDGE
        """
        q = query.strip().lower()

        # Check explicit general patterns first
        for pat in cls.GENERAL_PATTERNS:
            if re.search(pat, q):
                return "GENERAL"

        # Check follow-ups if conversation history exists
        if conversation_context and len(conversation_context) > 0:
            for pat in cls.FOLLOW_UP_PATTERNS:
                if re.search(pat, q):
                    return "FOLLOW_UP_TO_CURRENT_TOPIC"

        # Check lookahead patterns
        for pat in cls.LOOKAHEAD_PATTERNS:
            if re.search(pat, q):
                return "LOOKAHEAD"

        # Check document citations
        for pat in cls.DOCUMENT_PATTERNS:
            if re.search(pat, q):
                return "DOCUMENT_SEARCH"

        # Check active well state
        for pat in cls.ACTIVE_WELL_PATTERNS:
            if re.search(pat, q):
                return "ACTIVE_WELL_ANALYSIS"

        # Check product questions
        for pat in cls.PRODUCT_PATTERNS:
            if re.search(pat, q) and not any(k in q for k in ["ahead", "loss", "stuck", "kick"]):
                return "PETRONEXUS_PRODUCT"

        # Check if petroleum/drilling keywords or well identifiers exist
        has_drilling_terms = (
            any(k in q for k in cls.DRILLING_KEYWORDS)
            or bool(re.search(r"oil\-[a-z0-9\-]+", q))
            or bool(re.search(r"well[\s\-]?[a-z0-9]+", q))
        )
        if has_drilling_terms:
            if any(term in q for term in ["offset", "nearby", "history", "historical", "experienced", "past"]):
                return "HISTORICAL_WELL_KNOWLEDGE"
            return "DRILLING_ENGINEERING"

        # If no drilling terms are present at all, treat as general question
        return "GENERAL"

query_classifier = QueryClassifier()
