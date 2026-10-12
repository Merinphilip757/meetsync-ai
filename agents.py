import os, re, json, random, hashlib
from concurrent.futures import ThreadPoolExecutor

INTERESTS = {
    "travel": ["travel", "trip", "backpack", "wander", "explore", "passport"],
    "fitness": ["gym", "run", "marathon", "yoga", "lift", "cycling", "hike"],
    "food": ["cook", "bake", "coffee", "foodie", "restaurant", "brunch", "chef"],
    "music": ["music", "guitar", "concert", "piano", "singer", "band", "vinyl"],
    "reading": ["book", "read", "novel", "writer", "poetry", "author"],
    "photography": ["photo", "camera", "lens", "edit"],
    "tech": ["ai", "ml ", "engineer", "code", "python", "startup", "data", "backend"],
    "art": ["art", "paint", "design", "sketch", "illustrat", "museum"],
    "movies": ["movie", "film", "cinema", "series", "anime"],
    "nature": ["trek", "mountain", "beach", "garden", "pets", "dog", "cat", "nature"],
    "gaming": ["game", "gaming", "chess", "esports"],
    "mindfulness": ["faith", "meditat", "mindful", "temple", "church"],
}
VALUES = {
    "ambition": ["ambiti", "career", "founder", "growth", "hustle", "lead"],
    "family": ["family", "parents", "home", "kids"],
    "creativity": ["creative", "create", "writer", "design", "art", "music"],
    "stability": ["stable", "consistent", "routine", "planner", "reliable"],
    "adventure": ["adventure", "spontaneous", "travel", "explore", "trek"],
    "kindness": ["kind", "empath", "volunteer", "community", "care"],
    "curiosity": ["learn", "curious", "research", "read", "study"],
}
NEED_TEXT = {
    "ambition": "a partner who respects drive and long work stretches",
    "family": "someone who values family time and long-term commitment",
    "creativity": "room to create, and a partner who appreciates it",
    "stability": "reliability, clear plans and emotional consistency",
    "adventure": "a partner up for spontaneous plans and travel",
    "kindness": "warmth, empathy and a kind communicator",
    "curiosity": "deep conversation and a partner who keeps learning",
}
CITY_RE = re.compile(r"\b(chennai|mumbai|bangalore|bengaluru|delhi|hyderabad|pune|kochi|dubai|london|toronto|singapore)\b", re.I)


def _hits(text, lex):
    t = text.lower()
    return {k: sum(t.count(w) for w in ws) for k, ws in lex.items() if any(w in t for w in ws)}


def analyze(person):
    """Profile from ONLY the text the person supplied (LinkedIn about + Instagram bio/captions)."""
    text = f"{person.get('linkedin_text','')}\n{person.get('instagram_text','')}"
    ih, vh = _hits(text, INTERESTS), _hits(text, VALUES)
    interests = sorted(ih, key=ih.get, reverse=True)[:6]
    values = sorted(vh, key=vh.get, reverse=True)[:3]
    city = CITY_RE.search(text)
    prof = {
        "interests": interests,
        "values": values,
        "needs": [NEED_TEXT[v] for v in values],
        "hobbies": [i for i in interests if i not in ("tech",)][:4],
        "city": city.group(1).title() if city else "Unknown",
        "career_signal": "high" if vh.get("ambition", 0) >= 2 else "moderate",
        "social_style": "expressive" if text.count("!") + text.lower().count("love") >= 3 else "reserved",
        "summary": "",
    }
    prof["summary"] = (f"{person['name']} leans toward {', '.join(values) or 'balanced values'}; "
                       f"into {', '.join(interests) or 'a mix of things'}; based in {prof['city']}.")
    llm = _llm(
        "Return ONLY JSON with keys needs(list), hobbies(list), interests(list), values(list), "
        "social_style, summary. Analyze this person from the text they supplied:\n" + text[:4000])
    if llm:
        try:
            prof.update({k: v for k, v in json.loads(_json(llm)).items() if k in prof and v})
        except Exception:
            pass
    return prof


def _jac(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0


def heuristic_score(pa, pb):
    a, b = pa["profile"], pb["profile"]
    s = 0.5 * _jac(a["interests"], b["interests"]) + 0.3 * _jac(a["values"], b["values"])
    s += 0.1 * (a["city"] == b["city"] != "Unknown") + 0.1 * (a["career_signal"] == b["career_signal"])
    return round(min(s * 130, 100))


def _json(s):
    m = re.search(r"\{.*\}", s, re.S)
    return m.group(0) if m else s


def llm_provider():
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return None


def _groq(prompt):
    import urllib.request
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps({"model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                         "messages": [{"role": "user", "content": prompt}],
                         "temperature": 0.7, "max_tokens": 900}).encode(),
        headers={"Authorization": "Bearer " + os.environ["GROQ_API_KEY"],
                 "Content-Type": "application/json", "User-Agent": "meet-sync/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def _llm(prompt):
    prov = llm_provider()
    if prov is None:
        return None
    if prov == "groq":
        try:
            return _groq(prompt)
        except Exception:
            return None
    key = os.getenv("ANTHROPIC_API_KEY")
    try:
        import anthropic
        r = anthropic.Anthropic(api_key=key).messages.create(
            model=os.getenv("MODEL", "claude-sonnet-4-5"), max_tokens=900,
            messages=[{"role": "user", "content": prompt}])
        return r.content[0].text
    except Exception:
        return None


def _template_date(a, b, base):
    shared = sorted(set(a["profile"]["interests"]) & set(b["profile"]["interests"]))
    sv = sorted(set(a["profile"]["values"]) & set(b["profile"]["values"]))
    A, B = a["name"], b["name"]
    topic = shared[0] if shared else (a["profile"]["interests"] or ["life"])[0]
    t = [
        (A, f"Hi {B}! My person is into {', '.join(a['profile']['interests'][:3])}. What are they looking for?"),
        (B, f"Mine wants {(b['profile']['needs'] or ['something real'])[0]}. Is that something yours offers?"),
        (A, f"Mine looks for {(a['profile']['needs'] or ['connection'])[0]}. " +
            (f"We both seem to share {topic}." if shared else f"We differ on interests, but {topic} could be a bridge.")),
        (B, ("Shared values: " + ", ".join(sv) + ". " if sv else "Values differ a bit. ") +
            f"I'd rate this {base}/100. Date night around {topic}?"),
    ]
    return [{"speaker": s, "text": x} for s, x in t]


def date(a, b, use_llm=True):
    base = heuristic_score(a, b)
    turns, chem, mode = _template_date(a, b, base), base, "template"
    if use_llm:
        out = _llm(
            "Simulate a 6-turn first date between two AI agents, each representing their person. "
            "Stay strictly within their profiles; no invented facts.\n"
            f"AGENT A ({a['name']}): {json.dumps(a['profile'])}\nAGENT B ({b['name']}): {json.dumps(b['profile'])}\n"
            'Return ONLY JSON: {"transcript":[{"speaker":name,"text":str}],"chemistry":0-100,"reason":str}')
        if out:
            try:
                j = json.loads(_json(out))
                turns, chem, mode = j["transcript"], round((base + float(j["chemistry"])) / 2), "llm"
            except Exception:
                pass
    return {"a": a["id"], "b": b["id"], "transcript": turns, "score": chem, "mode": mode}


def run_all(people, use_llm=True):
    pairs = [(people[i], people[j]) for i in range(len(people)) for j in range(i + 1, len(people))]
    with ThreadPoolExecutor(8) as ex:
        dates = list(ex.map(lambda p: date(p[0], p[1], use_llm), pairs))
    rankings = {p["id"]: [] for p in people}
    for d in dates:
        rankings[d["a"]].append({"id": d["b"], "score": d["score"]})
        rankings[d["b"]].append({"id": d["a"], "score": d["score"]})
    for k in rankings:
        rankings[k].sort(key=lambda x: -x["score"])
    return dates, rankings


FIRST = ["Aarav", "Diya", "Kabir", "Meera", "Rohan", "Isha", "Arjun", "Nisha", "Vikram", "Anaya", "Dev", "Tara",
         "Neil", "Riya", "Karan", "Sana", "Ishaan", "Leela", "Yash", "Pooja", "Aditya", "Mira", "Samar", "Zoya", "Varun"]
BITS = ["I love to travel and trek on weekends!", "Marathon runner and gym regular.", "Coffee, baking and brunch spots.",
        "Play guitar, love concerts and vinyl.", "Always reading a novel, I also write poetry.",
        "Photography and photo editing are my escape.", "Backend engineer building AI and data products.",
        "Illustrator, museum regular, sketch daily.", "Movie and anime nights, film buff.",
        "Dog parent, garden and mountain beaches.", "Chess and gaming with friends.", "Meditation and temple visits keep me calm.",
        "Ambitious founder, career-driven, love growth.", "Family comes first, close to my parents.",
        "Kind, community volunteer, care deeply.", "Curious learner, research and study every day.",
        "Spontaneous, up for any adventure.", "Reliable planner, love a stable routine."]
CITIES = ["Chennai", "Bengaluru", "Mumbai", "Dubai", "Hyderabad"]


def demo_personas(n=25):
    out = []
    for i in range(n):
        r = random.Random(i * 7919)
        bits = r.sample(BITS, 4)
        out.append({"name": FIRST[i % len(FIRST)], "synthetic": True,
                    "linkedin_url": f"https://www.linkedin.com/in/demo-{i}",
                    "instagram_url": f"https://www.instagram.com/demo_{i}",
                    "linkedin_text": f"{bits[0]} {bits[1]} Based in {r.choice(CITIES)}.",
                    "instagram_text": f"{bits[2]} {bits[3]}"})
    return out
