import gradio as gr
import os
import urllib.parse
import base64
import requests
from bs4 import BeautifulSoup
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY") or "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")

PAK_DB = """
VERIFIED LEGIT PAKISTAN COMPANIES:
- Systems Limited (hr@systemslimited.com)
- Netsol Technologies (netsol.com)
- Arpatech (arpatech.com)
- TRG Pakistan (trgworld.com)
- Contour Software (contour.com)
- Folio3 (folio3.com)
- DevLogix (devlogix.com)
- Sybrid Pakistan (sybrid.com)
- 10Pearls (10pearls.com)
- HBL (hbl.com)
- MCB Bank (mcb.com.pk)
- Jazz (jazz.com.pk)
- Telenor Pakistan (telenor.com.pk)
- PTCL (ptcl.com.pk)
- Engro Corporation (engro.com)
- National Bank of Pakistan (nbp.com.pk)

CONFIRMED PAKISTAN SCAMS - ALWAYS VERDICT SCAM:
- Market65 / market65.space
- The Developers Arena
- Sysslan
- Fake Accenture posts
- Any .space or .xyz domain
- iamscientist fake internships
"""

SYSTEM_PROMPT = """You are PakJobAI, Pakistan's smartest AI job scam detector.

""" + PAK_DB + """

Analyze the job posting and respond in this EXACT format:

VERDICT: [SCAM / LEGIT / SUSPICIOUS]
CONFIDENCE: [0-100]%
COMPANY STATUS: [Verified Real / Unknown / Likely Fake]

RED FLAGS:
- [flag 1]

LEGIT SIGNALS:
- [signal 1]

SUMMARY (Roman Urdu mein):
[2-3 lines]

ADVICE (Roman Urdu):
[1-2 lines]
"""

reported_scams = []

def fetch_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return text[:3000]
    except:
        return ""

def analyze_text(job_text, language):
    lang_note = {
        "Roman Urdu": "Apna SARA response Roman Urdu mein do.",
        "English": "Give your ENTIRE response in English.",
        "Mix": "Mix Roman Urdu and English."
    }
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + "\n" + lang_note.get(language, "")},
            {"role": "user", "content": f"Analyze:\n\n{job_text}"}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

def analyze_image_with_groq(image_path):
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                {"type": "text", "text": "Extract all text from this job posting image. Return ONLY the extracted text."}
            ]
        }],
        max_tokens=1000
    )
    return response.choices[0].message.content

def process_input(job_url, job_text, image, language):
    final_text = ""
    prefix_note = ""

    if not job_url.strip() and not job_text.strip() and image is None:
        return "Kuch toh dalo — URL, text ya screenshot!", 0, ""

    try:
        if job_url.strip():
            fetched = fetch_url(job_url.strip())
            if fetched:
                final_text = fetched
                prefix_note = "[URL se fetch kiya gaya]\n"
            else:
                return "URL se data fetch nahi ho saka. Text manually paste karo!", 0, ""
        elif image is not None:
            extracted = analyze_image_with_groq(image)
            final_text = extracted
            prefix_note = f"[Screenshot se extract kiya gaya]\n{extracted}\n\n"
        else:
            final_text = job_text

        result = analyze_text(final_text, language)

        score = 50
        for line in result.split('\n'):
            if 'CONFIDENCE:' in line:
                try:
                    score = int(''.join(filter(str.isdigit, line.split(':')[1][:5])))
                except:
                    score = 50

        if "VERDICT: SCAM" in result:
            prefix = "SCAM DETECTED!\n\n"
            verdict_type = "SCAM"
        elif "VERDICT: LEGIT" in result:
            prefix = "LEGIT JOB!\n\n"
            verdict_type = "LEGIT"
            score = 100 - score
        else:
            prefix = "BE CAREFUL!\n\n"
            verdict_type = "SUSPICIOUS"

        full_result = prefix + prefix_note + result
        wa_text = f"PakJobAI Result: {verdict_type} (Confidence: {score}%)\nCheck: https://huggingface.co/spaces/summaya-shaikh/PakJobAI"
        wa_link = f"https://wa.me/?text={urllib.parse.quote(wa_text)}"

        return full_result, score, wa_link

    except Exception as e:
        return f"Error: {str(e)}", 0, ""

def report_scam(job_text):
    if job_text.strip():
        reported_scams.append(job_text[:100])
        return f"Shukriya! {len(reported_scams)} scams reported ab tak."
    return "Pehle job posting paste karo!"

examples = [
    ["", "Urgent hiring! Earn $500-$2000 weekly from home. No experience needed. WhatsApp: 0300-1234567.", None, "Roman Urdu"],
    ["", "Software Engineer at Systems Limited Lahore. Salary: 80,000-120,000 PKR. Apply: hr@systemslimited.com", None, "English"],
    ["", "Market65 internship - Work from home. Register at market65.space. Fee: 500 Rs only!", None, "Roman Urdu"],
]

with gr.Blocks(title="PakJobAI") as demo:
    gr.HTML("""
    <div style='text-align:center; padding:20px; background:linear-gradient(135deg,#0a0a2e,#1a1a4e); border-radius:15px; margin-bottom:20px;'>
        <h1 style='color:#00ff88; font-size:2.5em; margin:0;'>🇵🇰 PakJobAI</h1>
        <h3 style='color:#00aaff;'>Pakistan Job Scam Detector — AI Powered</h3>
        <p style='color:#aaa;'>Built by a Pakistani student who faced scams — so you don't have to.</p>
        <div style='background:#1a3a1a; border:1px solid #00ff88; border-radius:10px; padding:10px; margin:10px auto; max-width:700px;'>
            <p style='color:#00ff88; margin:0;'>✅ Free | 🔒 No data stored | ⚡ Instant AI | 📸 Screenshot | 🔗 URL support | 🇵🇰 Roman Urdu</p>
        </div>
    </div>
    """)

    with gr.Row():
        with gr.Column():
            job_url = gr.Textbox(
                lines=1,
                placeholder="Job URL paste karo (LinkedIn, Rozee.pk, Indeed)...",
                label="🔗 Job URL (Optional)"
            )
            job_input = gr.Textbox(
                lines=5,
                placeholder="Ya job posting text yahan paste karo...",
                label="📋 Job Posting Text"
            )
            image_input = gr.Image(
                type="filepath",
                label="📸 Ya Job Screenshot Upload Karo"
            )
            language = gr.Radio(
                choices=["Roman Urdu", "English", "Mix"],
                value="Roman Urdu",
                label="🌐 Response Language"
            )
            with gr.Row():
                clear_btn = gr.Button("🗑️ Clear", variant="secondary")
                submit_btn = gr.Button("🔍 Analyze!", variant="primary")
            report_btn = gr.Button("🚨 Is Job ko Scam Report Karo", variant="stop")
            report_output = gr.Textbox(label="Report Status", lines=1)

        with gr.Column():
            output = gr.Textbox(lines=12, label="🤖 PakJobAI Analysis")
            scam_score = gr.Slider(minimum=0, maximum=100, value=0,
                label="🎯 Scam Risk Score (0=Safe, 100=Definite Scam)", interactive=False)
            wa_link = gr.Textbox(label="📱 WhatsApp Share Link", lines=1)

    gr.Examples(examples=examples, inputs=[job_url, job_input, image_input, language])

    gr.HTML("""
    <div style='text-align:center; margin-top:20px; padding:15px; background:#1a1a3a; border-radius:10px;'>
        <p style='color:#ff6b6b;'>⚠️ Confirmed Scams: Market65 | The Developers Arena | Sysslan | Fake Accenture</p>
        <p style='color:#aaa; font-size:0.8em;'>PakJobAI by Summaya Shaikh — SALU CS Final Year | github.com/summayashaikh079-stack</p>
    </div>
    """)

    submit_btn.click(fn=process_input, inputs=[job_url, job_input, image_input, language], outputs=[output, scam_score, wa_link])
    clear_btn.click(fn=lambda: ("", "", None, "", 0, ""), outputs=[job_url, job_input, image_input, output, scam_score, wa_link])
    report_btn.click(fn=report_scam, inputs=[job_input], outputs=[report_output])

if __name__ == "__main__":
    demo.launch()