import re, uuid
from flask import Flask, jsonify, request, render_template
try:
    from dotenv import load_dotenv
    load_dotenv()  
except ImportError:
    pass
import agents

app = Flask(__name__)
STATE = {"people": {}, "dates": [], "rankings": {}}

LI = re.compile(r"^https?://([a-z]{2,3}\.)?linkedin\.com/in/[\w\-%.]+/?$", re.I)
IG = re.compile(r"^https?://(www\.)?instagram\.com/[\w.]+/?$", re.I)


def public_state():
    return {"people": list(STATE["people"].values()), "dates": STATE["dates"], "rankings": STATE["rankings"]}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def state():
    return jsonify(public_state())


@app.post("/api/people")
def add_person():
    d = request.get_json(force=True)
    if not d.get("consent"):
        return jsonify(error="Consent required: you must confirm these are your own profiles."), 400
    name = (d.get("name") or "").strip()
    li, ig = (d.get("linkedin_url") or "").strip(), (d.get("instagram_url") or "").strip()
    if not name:
        return jsonify(error="Name is required."), 400
    if not LI.match(li):
        return jsonify(error="LinkedIn link must look like https://www.linkedin.com/in/your-handle"), 400
    if not IG.match(ig):
        return jsonify(error="Instagram link must look like https://www.instagram.com/your_handle"), 400
    if not (d.get("linkedin_text") or d.get("instagram_text")):
        return jsonify(error="Paste your LinkedIn About and/or Instagram bio/captions so the agent has something to read."), 400
    p = {"id": uuid.uuid4().hex[:8], "name": name, "linkedin_url": li, "instagram_url": ig,
         "linkedin_text": d.get("linkedin_text", ""), "instagram_text": d.get("instagram_text", ""),
         "synthetic": False}
    p["profile"] = agents.analyze(p)
    STATE["people"][p["id"]] = p
    STATE["dates"], STATE["rankings"] = [], {}
    return jsonify(p)


@app.delete("/api/people/<pid>")
def delete_person(pid):
    STATE["people"].pop(pid, None)
    STATE["dates"], STATE["rankings"] = [], {}
    return jsonify(ok=True)


@app.post("/api/demo")
def demo():
    for i, p in enumerate(agents.demo_personas(25)):
        p["id"] = f"demo{i:02d}"
        p["profile"] = agents.analyze(p)
        STATE["people"][p["id"]] = p
    STATE["dates"], STATE["rankings"] = [], {}
    return jsonify(public_state())


@app.post("/api/run")
def run():
    people = list(STATE["people"].values())
    if len(people) < 2:
        return jsonify(error="Add at least 2 people first."), 400
    use_llm = bool((request.get_json(silent=True) or {}).get("use_llm"))
    STATE["dates"], STATE["rankings"] = agents.run_all(people, use_llm)
    return jsonify(public_state())


@app.post("/api/reset")
def reset():
    STATE.update(people={}, dates=[], rankings={})
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
