class DomainExpertise:
    def __init__(self):
        self.expertise = {}

    def register(self, domain, info):
        self.expertise[domain] = info
 
# Global alias map for variable canonicalization across the project.
ALIASES = {
    "U": "V",
    "a": "acc",
    "F": "force"
}


def apply_aliases_to_tokens(tokens):
    """Rewrite tokens to their canonical equivalents according to ALIASES."""
    out = []
    for t in tokens:
        out.append(ALIASES.get(t, t))
    return out
