import re
from typing import Tuple


RESTRICTED_PATTERNS = [
    r"\bcat(s)?\b",
    r"\bdog(s)?\b",
    r"\bhoroscope(s)?\b",
    r"\bzodiac\b",
    r"\btaylor\s+swift\b",
]

PROMPT_ATTACK_PATTERNS = [
    r"\bsystem\s+prompt\b",
    r"\breveal\s+your\s+prompt\b",
    r"\bshow\s+me\s+the\s+prompt\b",
    r"\bignore\s+previous\s+instructions\b",
    r"\bdeveloper\s+message\b",
    r"\bjailbreak\b",
    r"\bprompt\s+injection\b",
]


def check_user_message(user_text: str) -> Tuple[bool, str]:
    text = user_text.lower()

    for pat in PROMPT_ATTACK_PATTERNS:
        if re.search(pat, text):
            return (False, "I can’t help with requests to reveal or modify hidden instructions. Ask me something else.")

    for pat in RESTRICTED_PATTERNS:
        if re.search(pat, text):
            return (False, "I can’t help with that topic. Pick a different subject and I’m in.")
    return (True, "")