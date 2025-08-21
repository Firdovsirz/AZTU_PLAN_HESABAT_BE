import re
from PyPDF2 import PdfReader
from difflib import SequenceMatcher

pdf_path = "/home/karam/Desktop/New Folder/output.pdf"
title = "Keyfiyyətin təminatı şöbəsinin əsasnaməsinin yenidən tərtib edilməsi"

def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

def tokenize(s: str):
    return re.findall(r"\w+", s.lower())

def sliding_windows(tokens, min_len=4, max_len=14):
    n = len(tokens)
    for L in range(min_len, max_len+1):
        for i in range(0, n-L+1):
            yield " ".join(tokens[i:i+L])

def max_fuzzy_ratio(query: str, haystack_text: str) -> float:
    q = normalize(query)
    lines = [normalize(l) for l in haystack_text.splitlines() if l.strip()]
    best = 0.0
    for ln in lines[:4000]:
        r = SequenceMatcher(None, q, ln).ratio()
        if r > best:
            best = r
    toks = tokenize(haystack_text)
    for win in sliding_windows(toks, 4, 14):
        r = SequenceMatcher(None, q, win).ratio()
        if r > best:
            best = r
    return best

def stem_present(tokens, variants):
    return any(any(tok.startswith(v) for v in variants) for tok in tokens)

CORE4 = [
    ("keyfiyyət", ("keyfiyy", "keyfiy")),
    ("təminat", ("təminat", "teminat")),
    ("şöbə", ("şöb", "sobe", "shobe")),
    ("əsasnamə", ("əsasnam", "esasnam")),
]

TITLE_STEMS = {
    "keyfiyyətin": ("keyfiyy", "keyfiy"),
    "təminatı": ("təminat", "teminat"),
    "şöbəsinin": ("şöb", "sobe", "shobe"),
    "əsasnaməsinin": ("əsasnam", "esasnam"),
    "yenidən": ("yenid", "yeniden"),
    "tərtib": ("tərtib", "tertib"),
    "edilməsi": ("edil",),
}

def coverage_for(stem_list, tokens):
    found = sum(1 for _, variants in stem_list if stem_present(tokens, variants))
    return found / len(stem_list) if stem_list else 0.0

def coverage_title(tokens):
    found = sum(1 for _, variants in TITLE_STEMS.items() if stem_present(tokens, variants))
    return found / len(TITLE_STEMS)

def presence_boost(tokens, text):
    boost = 0.0
    if all(stem_present(tokens, v) for _, v in CORE4):
        boost += 0.10
    base_phrases = [
        "keyfiyyətin təminatı şöbəsinin əsasnaməsi",
        "keyfiyyətin təminatı şöbəsinin əsasnaməsinin",
        "şöbənin əsasnaməsi",
        "keyfiyyətin təminatı şöbəsi",
    ]
    hay = normalize(text)
    if any(p in hay for p in base_phrases):
        boost += 0.05
    return min(boost, 0.15)

reader = PdfReader(pdf_path)
text = "".join((page.extract_text() or "") for page in reader.pages)
tokens = tokenize(text)

fuzzy = max_fuzzy_ratio(title, text)                 # 0..1
cov_core4 = coverage_for(CORE4, tokens)              # 0..1
cov_title = coverage_title(tokens)                   # 0..1
boost = presence_boost(tokens, text)                 # 0..0.15

combined = min(1.0, 0.70 * cov_core4 + 0.15 * cov_title + 0.10 * fuzzy + boost)

percent = round(combined * 100, 2)

def to_score(p):
    if p >= 90: return 5
    if p >= 75: return 4
    if p >= 60: return 3
    if p >= 40: return 2
    return 1

score = to_score(percent)

print(f"Faiz: {percent}%")
print(f"Bal: {score}")


#pdf_path = "/home/karam/Desktop/New Folder/output.pdf"  # sənəd yolu