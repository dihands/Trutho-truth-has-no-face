import random

ADJECTIVES = [
    "Silent", "Hidden", "Ghost", "Echo", "Shadow", "Void", "Masked",
    "Veiled", "Cloaked", "Invisible", "Nameless", "Faceless", "Secret",
    "Covert", "Unseen", "Phantom", "Null", "Dark", "Blind", "Hollow",
    "Muted", "Cipher", "Stealth", "Cryptic", "Rogue", "Free", "True",
    "Brave", "Bold", "Clear", "Open", "Raw", "Pure", "Safe"
]

NOUNS = [
    "Witness", "Signal", "Citizen", "Truth", "Voice", "Watch", "Observer",
    "Reporter", "Source", "Sentinel", "Guard", "Seeker", "Finder", "Carrier",
    "Beacon", "Chronicle", "Record", "Account", "Dispatch", "Network",
    "Thread", "Link", "Node", "Trace", "Mark", "Echo", "Pulse", "Agent",
    "Entity", "Ghost", "Shadow", "Whisper", "Spark"
]


def generate_anonymous_username() -> str:
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    num = random.randint(100, 9999)
    return f"{adj}{noun}_{num}"
