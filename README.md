# PakJobAI 🇵🇰

**AI-powered job scam detector for Pakistan.** Paste a job posting (or its URL), get an instant verdict — scam or legit — with a confidence score, specific red flags, and a plain-language summary in Roman Urdu.

**Live app:** https://huggingface.co/spaces/summaya-shaikh/PakJobAI
**Source:** https://github.com/summayashaikh079-stack/PakJobAI

Built by Summaya Shaikh after encountering fake internship postings firsthand — so other Pakistani job seekers don't have to guess.

---

## Who it's for

Pakistani students and job seekers screening internship or job postings they found on Facebook, WhatsApp groups, LinkedIn, or job boards — before handing over money, personal documents, or bank details to a "registration fee" scam.

## What it does

1. You give it a job posting — paste the text, paste a URL, or (when available) upload a screenshot.
2. It checks the posting against a small list of known-legit Pakistani employers and known scam patterns, then sends it to an LLM with a scam-detection prompt.
3. It returns:
   - **Verdict:** Scam / Legit / Suspicious
   - **Confidence score** (0–100)
   - **Company status** (verified / likely fake / unknown)
   - **Red flags**, listed specifically (not just "be careful")
   - **A Roman Urdu summary** — so the reasoning is understandable to the actual audience, not just English-fluent users
   - A **pre-filled WhatsApp share link** so a user can forward the verdict to a friend in one tap

## Setup a stranger could follow

**Fastest way — no setup at all:** open the live Space above and paste a job posting.

**To run it locally:**

```bash
git clone https://github.com/summayashaikh079-stack/PakJobAI.git
cd PakJobAI
pip install -r requirements.txt
```

You need a free [Groq API key](https://console.groq.com/keys). Set it as an environment variable — **never hardcode it in the source**:

```bash
export GROQ_API_KEY="your-key-here"      # macOS/Linux
setx GROQ_API_KEY "your-key-here"        # Windows
```

Then run:

```bash
python app.py
```

Gradio will print a local URL (usually `http://127.0.0.1:7860`) — open it in your browser.

## Usage examples

**Paste text directly:**
```
Urgent Hiring! Work from home, earn $800-$1500 weekly. No experience needed,
no interview required. Just pay Rs. 500 registration fee to start immediately.
```
→ Verdict: **SCAM**, ~95% confidence. Red flags: no company named, unrealistic pay for zero experience, upfront fee requested, no interview process, contact via personal WhatsApp number only.

**Paste a job URL:** the app fetches and reads the page text automatically — no need to copy-paste manually.

**Legit posting from a known company** (e.g. an @systemslimited.com job): flagged as verified/legit with a much lower risk score, since the sender domain matches a company on the built-in verified list.

## Architecture

```
User input (text / URL / screenshot)
        |
        v
 process_input()
   |- if URL   -> fetch_url() -> scrape page text with requests + BeautifulSoup
   |- if text  -> used directly
   `- if image -> analyze_image_with_groq() [currently disabled, see Limitations]
        |
        v
 analyze_text()
   |- builds SYSTEM_PROMPT = base instructions + PAK_DB
   |     (PAK_DB = hardcoded list of verified real Pakistani employers
   |      and known confirmed scam companies/domains)
   `- sends prompt + job text to Groq chat completion API
        |
        v
 Groq LLM returns structured verdict
        |
        v
 Gradio UI displays: verdict, confidence, red flags,
 Roman Urdu summary, WhatsApp share link
```

No database, no user accounts, no server-side storage — every analysis is stateless and nothing the user submits is saved.

## Eval results (v2)

Manually tested across a small set of representative postings:

| Test case | Expected | Result |
|---|---|---|
| Upfront-fee "work from home" posting, no company named | Scam | Scam, 95% confidence |
| Posting from a domain on the verified-employer list | Legit | Legit, low risk score |
| Posting matching a known confirmed-scam company name | Scam | Scam, high confidence, flagged by name match |
| Vague posting with no company name but no upfront-fee ask | -- | Correctly flagged "Suspicious," not overclaimed as definite scam |

There is no large labeled benchmark dataset behind this — evaluation so far is scenario-based manual testing, not a held-out test set with precision/recall numbers. That's a real gap, listed below.

## Limitations

- **No formal accuracy benchmark.** Testing has been manual and scenario-based, not measured against a labeled dataset. A confident-sounding verdict is not a guarantee.
- **Screenshot upload is currently disabled.** Groq retired the vision model this app originally used (`llama-4-scout`) and doesn't currently offer a replacement on the free tier. The app now returns a clear message asking users to paste text instead, rather than silently failing. Text and URL input are unaffected.
- **The verified/scam company list is small and hardcoded.** It covers well-known large employers and a handful of confirmed scams -- it can't recognize companies outside that list by name alone; the LLM's general reasoning fills the gap, but that reasoning can be wrong.
- **English + Roman Urdu only.** Postings in pure Urdu script or regional languages aren't specifically tested.
- **No persistent tracking of newly discovered scams.** Each session starts from the same static list -- the app doesn't learn from prior user reports.
- **LLM-dependent.** Verdicts rely on an underlying language model's judgment; like any LLM output, it can occasionally be wrong or inconsistent between runs on borderline cases.

## Built with AI -- transparency note

This project was built with Claude (Anthropic) as a coding assistant: drafting and debugging `app.py`, fixing a security issue (an exposed API key that had been hardcoded as a fallback -- removed and replaced with an environment-variable-only setup), diagnosing a broken deployment after Groq retired the model this app depended on, and writing this README. I tested every fix myself against the live app before considering it done -- including the scam/legit test cases in the eval table above -- rather than assuming the code was correct because an AI wrote it.

## License

See `LICENSE` in this repository.
