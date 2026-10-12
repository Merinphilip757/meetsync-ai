# Meet Sync

**Every person gets an AI agent. The agents date each other. Everyone gets a ranked list of who fits them best.**

Meet Sync reads two sources per person, their LinkedIn and their Instagram, builds a profile (needs, hobbies, interests, values), sends each person's agent on a simulated date with every other agent, and ranks the matches.

> **Opt-in by design.** Each person pastes **their own** LinkedIn and Instagram links plus the text from their own profiles (About, headline, bio, captions) and ticks a consent box. The agent reads only what they supply. Nothing is scraped, and a profile can be deleted at any time.

---

## How it works

```
LinkedIn link + text  ─┐
                       ├─► Agent analyses the person ─► Profile page (needs, hobbies, interests, values)
Instagram link + text ─┘                                         │
                                                                 ▼
                                      Every agent dates every other agent (N people = N(N-1)/2 dates)
                                                                 │
                                                                 ▼
                                      Compatibility score per date ─► Ranking per person
```

1. **Add person**: name, own LinkedIn and Instagram links (format-checked), pasted profile text, consent checkbox.
2. **Profile**: the agent extracts interests, hobbies, values, needs, city, social style and career drive.
3. **Dates**: each pair of agents holds a short conversation on behalf of their people. Each date gets a 0-100 compatibility score.
4. **Rankings**: for every person, all others sorted by score, with shared interests and a link to the date that produced the score.

### Scoring
A rule-based score (interest overlap 50%, value overlap 30%, same city 10%, similar career drive 10%) is combined with the chemistry score from the date. If an LLM key is set, the LLM writes the analysis and the date dialogue. Without a key, a deterministic offline mode does both.

## Features

- Consent-gated sign-up with link validation
- Profile pages with the full analysis
- Run all dates in parallel (25 people = 300 dates)
- Transcript viewer for any pair
- Per-person rankings with shared interests
- Delete-my-profile, which resets dates and rankings
- 25 synthetic demo personas for a one-click demo
- Works fully offline with no API key

## Tech stack

- **Backend:** Python, Flask
- **Agents:** analysis and date simulation in `agents.py`; optional LLM through Groq (Llama 3.3 70B) or Anthropic
- **Frontend:** single-page HTML, CSS and vanilla JavaScript
- **Concurrency:** `ThreadPoolExecutor` runs all pairings in parallel
- **Input:** user-supplied links and pasted text, no scraping

## Project layout

```
agents.py            analysis, date simulation, scoring, ranking, demo personas
app.py               Flask API
templates/index.html UI
requirements.txt     dependencies
.env.example         copy to .env to add your API key
```

---

## Run locally (VS Code, Windows)

```powershell
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

### Optional: add an LLM key (Groq)
1. Copy `.env.example` to a new file named `.env`.
2. Put your key in it: `GROQ_API_KEY=gsk_your_key`
3. Restart `python app.py`, then tick **Use LLM for dialogue** on the Dates tab.

`.env` is listed in `.gitignore`, so it is never uploaded to GitHub. **Never put a key in the code.** The app runs without any key.

Check the key works:
```powershell
python -c "import agents; print(agents.llm_provider()); print(agents._llm('Say hi in 3 words'))"
```
It should print `groq` and a short reply. `None` on the second line means the key failed and the app will use offline mode.

## Test checklist

1. Open the site and click **Load 25 demo personas**: 25 profile cards appear.
2. Dates tab, click **Run all dates**: the counter shows 300.
3. Pick any two people: transcript and score appear.
4. Rankings tab, pick a person: sorted matches with scores.
5. Add person tab, submit without the consent box: an error appears.
6. Add your own profile with real links and pasted text: your profile card appears.
7. Delete a profile: dates and rankings reset.

---

## Upload to GitHub

1. Create an account at github.com, click **New repository**, name it `meet-sync`, set it to **Public**, and do not add a README (you already have one). Click **Create repository**.
2. In the VS Code terminal, in the project folder:
   ```powershell
   git init
   git add .
   git status
   ```
   Check that `.env` is **not** in the list. If it appears, stop and check `.gitignore`.
3. Then:
   ```powershell
   git commit -m "Meet Sync"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/meet-sync.git
   git push -u origin main
   ```
4. Refresh the GitHub page. The files should be there. The repo URL is your GitHub submission link.

## Deploy the live website

Meet Sync is a Flask app, so it needs a host that runs Python web servers. **Render** has a free tier.

1. Go to render.com, sign in with GitHub, and click **New +**, then **Web Service**.
2. Pick the `meet-sync` repo.
3. Settings:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn -w 1 -b 0.0.0.0:$PORT app:app`
   - **Instance type:** Free
4. (Optional) Under **Environment**, add `GROQ_API_KEY` with your key.
5. Click **Create Web Service**. After a few minutes you get a public URL like `https://meet-sync.onrender.com`. That is your **Live website** and **Demo link**.
6. Open the URL, click **Load 25 demo personas**, then **Run all dates**, so the demo is already run.

Notes:
- Keep `-w 1`. State is held in memory, so one worker keeps everything consistent.
- The free tier sleeps after inactivity, so the first load can take about a minute. Open it just before submitting.
- State resets when the service restarts. Re-run the demo if it does.

### About Streamlit
Streamlit Community Cloud only runs Streamlit scripts, not Flask apps. Use Render (above) for this project. Hosting it on Streamlit would need a separate Streamlit version of the UI.

---

## Submission text

**Overall explanation (200 characters):**
Meet Sync: each person's AI agent reads their own LinkedIn + Instagram text, builds a profile, dates every other agent in simulation, and ranks the best matches.

**Technical section:**
Opt-in input: people paste their own LinkedIn/Instagram links and profile text with consent; no scraping. Python + Flask backend, vanilla JS frontend. An LLM (Groq Llama 3.3 70B) extracts needs, hobbies, interests and values and writes agent-to-agent dates, with a rule-based offline fallback. A scorer blends interest/value/city overlap with date chemistry. ThreadPoolExecutor runs 300 pairings in parallel.

## 3-minute video outline

| Time | Show |
|------|------|
| 0:00-0:20 | What Meet Sync is, consent sign-up, creating an agent |
| 0:20-1:00 | Profile pages: needs, hobbies, interests, values for 2-3 people |
| 1:00-2:00 | Run all dates, open one transcript and its score |
| 2:00-2:40 | Rankings for one person, shared interests, jump to the date |
| 2:40-3:00 | Tech stack, delete-my-profile, repo link |

## Privacy

Meet Sync stores only what a person submits, in memory, and only until the server restarts or they delete their profile. It does not scrape LinkedIn or Instagram. The 25 demo personas are fictional.
