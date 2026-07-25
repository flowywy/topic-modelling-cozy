import re
import io
import math
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px

# Imported here (once, at module load) instead of inside is_english() —
# previously it was re-imported and re-seeded on every single row via
# .apply(), which is unnecessary repeated work for no benefit.
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 42  # deterministic language detection results

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cozy Review Analyzer",
    page_icon="💌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS — Cozy theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, h1, h2, h3, p, div {
    font-family: 'Nunito', sans-serif !important;
}
.stApp { background-color: #FDFAF6; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; }

.cozy-header { text-align: center; padding: 2.5rem 1rem 1.5rem 1rem; }
.cozy-header h1 { font-size: 2.4rem; font-weight: 800; color: #C1440E; margin-bottom: 0.3rem; }
.cozy-header p  { color: #8C6F5E; font-size: 1rem; font-weight: 500; }

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #FDF0EB;
    border-radius: 14px;
    padding: 16px 20px;
    border-left: 4px solid #C4714B;
}
[data-testid="stMetricLabel"] {
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    color: #8B4A2E !important;
    font-size: 0.8rem !important;
    text-transform: lowercase;
}
[data-testid="stMetricValue"] {
    font-family: 'Nunito', sans-serif !important;
    font-weight: 800 !important;
    color: #5C3D2E !important;
}

/* Buttons */
.stButton > button {
    background-color: #E76F51 !important; color: white !important;
    border: none !important; border-radius: 20px !important;
    font-family: 'Nunito', sans-serif !important; font-weight: 700 !important;
    font-size: 0.95rem !important; padding: 0.5rem 1.8rem !important;
    transition: background 0.2s ease !important;
}
.stButton > button:hover { background-color: #C1440E !important; }

/* Download button */
[data-testid="stDownloadButton"] > button {
    background-color: #FFF0EB !important; color: #C1440E !important;
    border: 1.5px solid #E76F51 !important; border-radius: 20px !important;
    font-family: 'Nunito', sans-serif !important; font-weight: 700 !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background-color: #E76F51 !important; color: white !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; justify-content: center; }
.stTabs [data-baseweb="tab"] {
    background-color: #FFF0EB; border-radius: 20px !important;
    border: 1.5px solid #F4C9B8 !important; color: #8C6F5E !important;
    font-family: 'Nunito', sans-serif !important; font-weight: 700 !important;
    padding: 0.4rem 1.4rem !important;
}
.stTabs [aria-selected="true"] { background-color: #E76F51 !important; color: white !important; border-color: #E76F51 !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none !important; background-color: transparent !important; }

[data-testid="stFileUploader"] { border: 2px dashed #F4C9B8 !important; border-radius: 16px !important; background: #FFF8F4 !important; padding: 1rem !important; }
.stTextInput > div > div > input, .stSelectbox > div > div { border-radius: 12px !important; border-color: #F4C9B8 !important; font-family: 'Nunito', sans-serif !important; }
.streamlit-expanderHeader { background-color: #FFF0EB !important; border-radius: 12px !important; font-weight: 700 !important; color: #8C6F5E !important; }
hr { border-color: #F4C9B8 !important; opacity: 0.5; }
[data-testid="stStatus"] { background-color: #FFF8F4 !important; border: 1.5px solid #F4C9B8 !important; border-radius: 16px !important; font-family: 'Nunito', sans-serif !important; }
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden; }
[data-testid="stAlert"] { border-radius: 12px !important; font-family: 'Nunito', sans-serif !important; }
.stCaption { color: #B08070 !important; font-family: 'Nunito', sans-serif !important; }
h2, h3 { color: #C1440E !important; }

/* Topic cards */
.topic-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:14px; margin:0.5rem 0; }
.topic-card { background:#FFF8F4; border-radius:16px; border:1.5px solid #F4C9B8; border-left:5px solid var(--accent); padding:14px 16px; box-shadow:0 2px 8px rgba(199,90,50,0.06); }
.topic-card h4 { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.88rem; color:#5C3D2E; margin:0 0 8px 0; }
.topic-card .meta { font-family:'Nunito',sans-serif; font-size:0.78rem; color:#8C6F5E; margin-bottom:8px; }
.sent-bar { display:flex; height:7px; border-radius:10px; overflow:hidden; margin-top:6px; }
.sent-pos { background:#E76F51; }
.sent-neu { background:#A8DADC; }
.sent-neg { background:#6D3B2E; }

/* Review cards */
.review-card { background:#FFF8F4; border:1.5px solid #F4C9B8; border-radius:14px; padding:14px 16px; margin-bottom:10px; }
.review-card .stars { color:#E76F51; font-size:0.85rem; letter-spacing:1px; }
.review-card .badge { display:inline-block; padding:2px 10px; border-radius:20px; font-size:0.72rem; font-weight:700; font-family:'Nunito',sans-serif; margin-left:8px; }
.badge-positive { background:#FDE8E2; color:#C1440E; }
.badge-neutral  { background:#E0F4F5; color:#2A7A7E; }
.badge-negative { background:#EDE0DC; color:#5C3D2E; }
.review-card p { font-family:'Nunito',sans-serif; font-size:0.88rem; color:#5C3D2E; margin:8px 0 0 0; line-height:1.55; }

/* Empty state */
.empty-state { text-align:center; padding:3rem 1rem; }
.empty-state h3 { color:#C1440E !important; font-size:1.2rem; }
.empty-state p  { font-size:0.92rem; color:#8C6F5E; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
TOPIC_LABELS = {
    0: "General Experience & Game Content",
    1: "Technical Performance",
    2: "Relaxing & Stress-Relief Experience",
    3: "Ads & Monetization",
    4: "Farm Life Simulation",
    5: "Account & Data Issues",
    6: "In-App Purchase & Pricing",
    7: "Immersive World & Social Play",
    8: "Nostalgia & Player Loyalty"
}

SENTIMENT_COLOR = {
    "positive": "#E76F51",
    "neutral":  "#A8DADC",
    "negative": "#6D3B2E",
}

CHART_COLORS = [
    "#E76F51", "#F4A261", "#E9C46A",
    "#A8DADC", "#457B9D", "#C77B58",
    "#8B5E52", "#D4A59A",
]

MAX_FETCH      = 2000
HARD_CAP       = 1500
BATCH_SIZE     = 32
DEFAULT_THRESH = 0.30

# ─────────────────────────────────────────────
# Cached resources
# ─────────────────────────────────────────────

# Words protected from lemmatization (kept in their original surface form)
# during c-TF-IDF tokenization — copied from the training notebook so the
# tokenizer below behaves identically to the one vectorizer_model was
# originally fit with.
PROTECTED = {
    'ads', 'levels', 'items', 'coins', 'gems', 'lives', 'hours', 'days',
    'bug', 'crash', 'crashes', 'lag', 'lags', 'fps', 'graphics',
    'offline', 'loading', 'server', 'storage', 'progress', 'save',
    'glitch', 'glitches', 'stuttering', 'optimization', 'battery', 'overheat',
    'connection', 'stuck', 'unplayable', 'farming', 'fishing', 'crafting',
    'cooking', 'harvesting', 'decorating',
    'multiplayer', 'tutorial', 'inventory', 'expensive', 'exploration', 'relaxing', 'gameplay',
    'addicting', 'entertaining', 'rewarding',
    'frustrating', 'satisfying', 'calming', 'soothing', 'engaging',
    'overwhelming', 'grind', 'wholesome', 'harvest', 'data',
}

# Populated by load_model() below. BERTopic's safetensors serialization
# can't pickle arbitrary Python functions, so the CountVectorizer's
# original `tokenizer=lemmatize_tokenizer` is lost when the model is
# reloaded from Hugging Face. sklearn's tokenizer contract only passes the
# document text (one argument), so this spaCy instance has to be reached
# through a module-level reference rather than a function parameter.
_lemma_nlp = None

def lemmatize_tokenizer(text):
    """
    Reproduces the exact tokenizer vectorizer_model was fit with during
    training. Reattached to the loaded model's vectorizer_model in
    load_model() so reduce_outliers(strategy="c-tf-idf") tokenizes new
    documents the same way training did, instead of falling back to
    sklearn's default token_pattern (which is None here and raises a
    TypeError since this vectorizer was always meant to use a custom
    tokenizer, never the regex-based default).
    """
    text = re.sub(r"(?<!\w)([xX;:]'?[dDpPvVoO3)(])(?!\w)", ' ', text)
    doc = _lemma_nlp(text)
    tokens = []
    for token in doc:
        if token.is_punct or (len(token.text) <= 2 and token.text.lower() != 'ad'):
            continue
        word_lower = token.text.lower()
        word = token.text if word_lower in PROTECTED else token.lemma_
        tokens.append(word.lower())
    return tokens

@st.cache_resource(show_spinner=False)
def load_model():
    import os
    # Windows restricts symlink creation to admins/Developer Mode by default,
    # which makes snapshot_download raise WinError 1314. Forcing HF Hub to
    # copy files instead of symlinking avoids that (slightly more disk usage).
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
    from bertopic import BERTopic
    from huggingface_hub import snapshot_download
    path = snapshot_download(repo_id="primvera11/cozy-games-bertopic")
    model = BERTopic.load(
        os.path.join(path, "model"),
        embedding_model="sentence-transformers/all-mpnet-base-v2",
    )

    # Reattach the custom tokenizer (see lemmatize_tokenizer docstring above)
    # so reduce_outliers(strategy="c-tf-idf") works instead of erroring.
    global _lemma_nlp
    _lemma_nlp = load_nlp()
    if model.vectorizer_model is not None:
        model.vectorizer_model.tokenizer = lemmatize_tokenizer

    return model

@st.cache_resource(show_spinner=False)
def load_nlp():
    import spacy
    try:
        return spacy.load("en_core_web_md", disable=["parser", "ner"])
    except OSError:
        from spacy.cli import download
        download("en_core_web_md")
        return spacy.load("en_core_web_md", disable=["parser", "ner"])

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def map_sentiment(score):
    if score in (4, 5): return "positive"
    elif score == 3:    return "neutral"
    return "negative"

def is_english(text):
    try:
        cleaned = str(text).strip()
        if len(cleaned) < 20:
            return False
        return detect(cleaned) == "en"
    except Exception:
        return False

def clean_text(text):
    text = str(text)
    text = re.sub(r'http\S+|www\S+|https\S+', ' ', text)
    text = re.sub(r'<.*?>|&\w+;', ' ', text)
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    text = re.split(r'(?i)edit[:\-]|\bupdate[:\-]', text)[0]
    text = re.sub(r"(?<!\w)([xX;:]'?[dDpPvVoO3)(])(?!\w)", ' ', text)
    text = re.sub(r'@[^\s]+|#(\S+)', r'\1', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'[\xad\u200b\u200c\u200d\ufeff]', '', text)
    text = re.sub(r'\b(\w+)(\s+\1\b)+', r'\1', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def preprocess_batch(texts, nlp, batch_size=64):
    """
    spaCy is built to process many documents at once via nlp.pipe() —
    calling nlp(text) one row at a time inside a pandas .apply() loop
    throws away spaCy's internal batching/buffering and is noticeably
    slower for anything more than a handful of rows. The regex cleanup
    step is cheap per-row and stays as a plain list comprehension; only
    the spaCy lemmatization step (the expensive part) is batched.
    """
    cleaned = [re.sub(r"\s+", " ", re.sub(r"[^a-z\s]", " ", clean_text(t))).strip() for t in texts]
    results = []
    for doc in nlp.pipe(cleaned, batch_size=batch_size):
        tokens = [t.lemma_ for t in doc if not t.is_stop and not t.is_punct and len(t.lemma_) > 2]
        results.append(" ".join(tokens))
    return results

# ─────────────────────────────────────────────
# PDF Generator
# ─────────────────────────────────────────────
def safe_str(text):
    """Strip non-ASCII characters (emoji, unicode) so Helvetica won't choke."""
    return text.encode("ascii", errors="ignore").decode("ascii").strip()
 
def section_header(pdf, text):
    """Header section berwarna terra cotta yang dipakai berulang di seluruh PDF."""
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(193, 68, 14)
    pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(60, 30, 15)

def generate_pdf(df, df_valid, summary_rows):
    from fpdf import FPDF
 
    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(193, 68, 14)
            self.cell(0, 10, "Cozy Review Analyzer - Analysis Report", align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(244, 201, 184)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
 
        def footer(self):
            self.set_y(-13)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(180, 130, 110)
            self.cell(0, 10, f"Page {self.page_no()} - generated by Cozy Review Analyzer", align="C")
 
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
 
    # — Summary section —
    section_header(pdf, "Summary")
    pdf.set_font("Helvetica", "", 10)

    meta = [
        ("Total reviews analyzed",  f"{len(df):,}"),
        ("Topics found",            str(df_valid['topic'].nunique())),
        ("Reviews set aside",       f"{(df['topic'] == -1).sum():,}"),
        ("Generated on",            datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
    ]
    for label, val in meta:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(70, 7, label + ":", border=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, val, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
 
    # — Sentiment breakdown —
    section_header(pdf, "Overall Sentiment")
    vc   = df["sentiment"].value_counts()
    tot  = len(df)
    for sent, color in [("positive", (231,111,81)), ("neutral", (168,218,220)), ("negative", (244, 162, 133))]:
        count = vc.get(sent, 0)
        pct   = count / tot * 100 if tot else 0
        pdf.set_fill_color(*color)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(40, 6, sent.capitalize(), border=1, fill=True)
        pdf.cell(30, 6, f"{count:,}", border=1, align="R")
        pdf.cell(30, 6, f"{pct:.1f}%", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
 
    # — Topic summary table —
    section_header(pdf, "Topic Summary")
    headers = ["Topic", "Reviews", "Positive", "Neutral", "Negative"]
    widths  = [86, 24, 26, 26, 26]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(255, 240, 235)
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, fill=True)
    pdf.ln()
 
    pdf.set_font("Helvetica", "", 9)
    for i, row in enumerate(summary_rows):
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(253, 250, 246)
        else:
            pdf.set_fill_color(255, 255, 255)
        vals = [row["topic"], str(row["reviews"]),
                row["positive %"], row["neutral %"], row["negative %"]]
        for val, w in zip(vals, widths):
            pdf.cell(w, 6, str(val)[:30], border=1, fill=fill)
        pdf.ln()
    pdf.ln(4)
 
    # — Top reviews per topic —
    section_header(pdf, "Top Reviews per Topic (highest confidence)")
    for tid, label in TOPIC_LABELS.items():
        subset = df_valid[df_valid["topic"] == tid].sort_values("probability", ascending=False).head(3)
        if len(subset) == 0:
            continue
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(255, 240, 235)
        pdf.cell(0, 7, label, border="B", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for _, r in subset.iterrows():
            review_text = safe_str(str(r["content"])[:500].replace("\n", " "))
            sent        = safe_str(r["sentiment"])
            prob        = r["probability"]
            pdf.set_text_color(140, 111, 94)
            pdf.cell(0, 5, f"[{sent} | confidence: {prob:.2f}]", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(60, 30, 15)
            pdf.multi_cell(0, 5, review_text)
            pdf.ln(1)
        pdf.ln(2)
 
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ─────────────────────────────────────────────
# UI Helpers
# ─────────────────────────────────────────────
def stars(score):
    n = int(round(float(score)))
    return "★" * n + "☆" * (5 - n)

def render_review_cards(df_subset):
    for _, r in df_subset.iterrows():
        sent  = r["sentiment"]
        text  = str(r["content"])[:400].replace("<","&lt;").replace(">","&gt;")
        st.markdown(f"""
        <div class="review-card">
            <span class="stars">{stars(r["score"])}</span>
            <span class="badge badge-{sent}">{sent}</span>
            <p>{text}</p>
        </div>
        """, unsafe_allow_html=True)

def render_topic_cards(summary_rows):
    cards = '<div class="topic-grid">'
    for i, row in enumerate(summary_rows):
        accent = CHART_COLORS[i % len(CHART_COLORS)]
        n      = row["reviews"]
        pos    = float(row["positive %"].replace("%",""))
        neu    = float(row["neutral %"].replace("%",""))
        neg    = float(row["negative %"].replace("%",""))
        cards += f"""<div class="topic-card" style="--accent:{accent}">
            <h4>{row["topic"]}</h4>
            <div class="meta">{n:,} reviews</div>
            <div class="sent-bar">
                <div class="sent-pos" style="width:{pos:.1f}%"></div>
                <div class="sent-neu" style="width:{neu:.1f}%"></div>
                <div class="sent-neg" style="width:{neg:.1f}%"></div>
            </div>
            <div class="meta" style="margin-top:5px">
                <span style="color:#E76F51">■</span> {row["positive %"]} positive &nbsp;
                <span style="color:#A8DADC">■</span> {row["neutral %"]} neutral &nbsp;
                <span style="color:#6D3B2E">■</span> {row["negative %"]} negative
            </div>
        </div>"""
    cards += '</div>'
    st.markdown(cards, unsafe_allow_html=True)

def centered(ratio=(1, 2, 1)):
    """Kolom tengah untuk konten yang ingin ditampilkan center (dipakai di Input & Settings/Run)."""
    _, col, _ = st.columns(ratio)
    return col

def render_empty_state():
    st.markdown("""
    <div class="empty-state">
        <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
            <ellipse cx="36" cy="58" rx="24" ry="5" fill="#F4C9B8" opacity="0.5"/>
            <rect x="12" y="22" width="48" height="32" rx="4" fill="#FFF0EB" stroke="#E76F51" stroke-width="2.5"/>
            <path d="M12 24 L36 42 L60 24" stroke="#E76F51" stroke-width="2.5" fill="none" stroke-linejoin="round" stroke-linecap="round"/>
            <circle cx="52" cy="16" r="3" fill="#E76F51" opacity="0.7"/>
        </svg>
        <h3>the mailbox is empty ˘ᵕ˘</h3>
        <p>upload a CSV or fetch reviews from Google Play<br>to start sorting through the mail</p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────
def run_pipeline(df_raw, threshold):
    status = st.status("opening the mailbag... ", expanded=True)

    with status:
        # Step 1 : hard cap
        if len(df_raw) > HARD_CAP:
            st.write(f"oh wow, that's a lot of letters! ✂ trimming the stack to {HARD_CAP:,} so things don't take too long")
            df_raw = df_raw.head(HARD_CAP)

        # Step 2 :language filter
        st.write("sifting through the letters... only English ones may pass the gate! (˶ᵔᵕᵔ˶)")
        df       = df_raw.dropna(subset=["content"]).copy()
        n_before = len(df)
        df["is_english"] = df["content"].apply(is_english)
        df = df[df["is_english"]].drop(columns=["is_english"]).reset_index(drop=True)
        st.write(f"found {len(df):,} English letters out of {n_before:,}, ready for reading! ♡")

        if len(df) == 0:
            status.update(label="hmm, no English letters found in this batch... (´• ω •`)", state="error")
            st.stop()

        # Step 3 : sentiment
        st.write("reading each letter closely... happy news or not? (´･ω･`)")
        df["sentiment"] = df["score"].apply(map_sentiment)

        # Step 4 : preprocess
        st.write("smoothing out the handwriting... tidying up the messy bits ˶ᵕ⤙ᵕ˶")
        nlp = load_nlp()
        # Batched via nlp.pipe() instead of a per-row .apply() — spaCy
        # processes the whole list together, which is faster than calling
        # nlp() one document at a time.
        df["content_cleaned"] = preprocess_batch(df["content"].tolist(), nlp)
        df = df[df["content_cleaned"].str.strip() != ""].reset_index(drop=True)

        # Step 5 : transform
        st.write("sorting each letter into its pigeonhole...")
        model     = load_model()
        docs      = df["content_cleaned"].tolist()
        n_batches = math.ceil(len(docs) / BATCH_SIZE)

        all_topics, all_probs = [], []
        batch_bar = st.progress(0, text="sorting bundle 1...")
        for i in range(n_batches):
            batch = docs[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
            t, p  = model.transform(batch)
            all_topics.extend(t)
            all_probs.extend(p if hasattr(p, "__iter__") else [p])
            batch_bar.progress(
                (i + 1) / n_batches,
                text=f"sorting bundle {i+1} of {n_batches}... almost there! (´▽`))",
            )
        batch_bar.empty()

        df["topic"]       = [t if p >= threshold else -1 for t, p in zip(all_topics, all_probs)]
        df["probability"] = all_probs

        # Step 5b : two-stage outlier reduction (mirrors the training/test
        # methodology: c-TF-IDF strategy first, then embeddings strategy for
        # whatever is still unassigned). This only touches documents that
        # are still topic == -1 after the confidence threshold above; every
        # other document keeps its original topic/probability untouched.
        # Note: "probability" still reflects the original similarity score
        # from Step 5, not a new confidence value for reassigned documents —
        # reduce_outliers() itself doesn't return updated probabilities.
        n_outliers_before = (df["topic"] == -1).sum()
        if n_outliers_before > 0:
            st.write(f"giving {n_outliers_before:,} unsorted letters a second look... (｡•ᴗ•｡)")
            topics_stage1 = model.reduce_outliers(
                docs, df["topic"].tolist(), strategy="c-tf-idf", threshold=0.2
            )
            topics_stage2 = model.reduce_outliers(
                docs, topics_stage1, strategy="embeddings", threshold=0.7
            )
            df["topic"] = topics_stage2

        df["topic_label"] = df["topic"].map(TOPIC_LABELS).fillna("Outlier")

        n_out = (df["topic"] == -1).sum()
        st.write(f"wrapping up... {n_out:,} letters didn't fit any pigeonhole, not every letter needs a slot! ✿")
        status.update(label="all sorted! your mail is ready to read ♡", state="complete")

    return df

# ─────────────────────────────────────────────
# UI — Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="cozy-header">
    <h1>✦ Cozy Review Analyzer ✦</h1>
    <p>drop your reviews in the mailbox and let's see what players have to say<br>
    only English reviews · trained on 8 cozy mobile games</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# UI — Input (centered tabs)
# ─────────────────────────────────────────────


center_col = centered()
with center_col:
    tab_csv, tab_id = st.tabs(["📂  Upload CSV", "🎮  Google Play App ID"])
    df_raw = None

    with tab_csv:
        st.write("")
        uploaded = st.file_uploader("drop your CSV here!", type=["csv"], label_visibility="collapsed")
        st.caption("needs two columns: `content` (review text) and `score` (1–5)")
        if uploaded:
            df_raw = pd.read_csv(uploaded)
            missing = [c for c in ["content", "score"] if c not in df_raw.columns]
            if missing:
                st.error(f"oops! missing columns: {missing}")
                df_raw = None
            else:
                st.success(f"got {len(df_raw):,} letters ready to sort! ♡")
                st.dataframe(df_raw.head(3), use_container_width=True)

    with tab_id:
        st.write("")
        app_id = st.text_input("App ID", placeholder="com.chucklefish.stardewvalley", label_visibility="collapsed")
        st.caption("find it in the Play Store URL: `play.google.com/store/apps/details?id=com.example.app`")

        n_fetch = st.number_input(
            "how many reviews to fetch?",
            min_value=50,
            max_value=MAX_FETCH,
            value=500,
            step=50,
            help=f"you can fetch up to {MAX_FETCH:,} reviews. the pipeline will process up to {HARD_CAP:,}.",
        )
        if n_fetch == MAX_FETCH:
            st.caption(f"that's the max we can fetch!")

        if st.button("fetch reviews!", use_container_width=True) and app_id:
            with st.spinner("heading to the Play Store... back in a moment! ˘ᵕ˘"):
                try:
                    from google_play_scraper import reviews, Sort
                    result, _ = reviews(
                        app_id, lang="en", country="us",
                        sort=Sort.NEWEST, count=int(n_fetch),
                    )
                    df_raw = pd.DataFrame(result)[["content", "score", "at"]]
                    st.success(f"picked up {len(df_raw):,} letters! let's take a peek ✿")
                    st.dataframe(df_raw.head(3), use_container_width=True)
                    st.session_state["df_raw"] = df_raw
                except Exception as e:
                    st.error(f"hmm, something went wrong: {e}")

        if df_raw is None and "df_raw" in st.session_state:
            df_raw = st.session_state["df_raw"]

# ─────────────────────────────────────────────
# UI — Settings & Run
# ─────────────────────────────────────────────
if df_raw is None and "df_result" not in st.session_state:
    render_empty_state()

if df_raw is not None:
    st.write("")
    with centered():
        if st.button("run analysis", type="primary", use_container_width=True):
            df_result = run_pipeline(df_raw, DEFAULT_THRESH)
            st.session_state["df_result"] = df_result
            st.session_state.pop("pdf_bytes", None)

# ─────────────────────────────────────────────
# UI — Results
# ─────────────────────────────────────────────
if "df_result" in st.session_state:
    df       = st.session_state["df_result"]
    df_valid = df[df["topic"] != -1].copy()



    st.divider()
    st.subheader("here's what we found ♡")

    df_view     = df_valid.copy()
    df_all_view = df.copy()

    st.write("")

    # ── Metrics 
    c1, c2, c3 = st.columns(3)
    c1.metric("reviews read",   f"{len(df_all_view):,}")
    c2.metric("topics found",   df_view["topic"].nunique())
    c3.metric("set aside",      f"{(df_all_view['topic'] == -1).sum():,}")

    st.divider()

    # Charts 
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Topic Distribution")
        tc = df_view["topic_label"].value_counts().reset_index()
        tc.columns = ["topic", "count"]
        fig1 = px.bar(tc, x="count", y="topic", orientation="h",
                      color="topic", color_discrete_sequence=CHART_COLORS)
        fig1.update_layout(showlegend=False, yaxis_title="", xaxis_title="number of reviews",
                           height=380, margin=dict(l=0, r=10, t=10, b=10),
                           plot_bgcolor="#FDFAF6", paper_bgcolor="#FDFAF6",
                           font=dict(family="Nunito", color="#5C3D2E"))
        st.plotly_chart(fig1, use_container_width=True)

    with col_r:
        st.subheader("Sentiment per Topic")
        sp = df_view.groupby(["topic_label", "sentiment"]).size().reset_index(name="count")
        fig2 = px.bar(sp, x="topic_label", y="count", color="sentiment",
                      barmode="stack", color_discrete_map=SENTIMENT_COLOR)
        fig2.update_layout(xaxis_tickangle=-30, xaxis_title="", yaxis_title="count",
                           height=380, legend_title="sentiment",
                           margin=dict(l=0, r=10, t=10, b=80),
                           plot_bgcolor="#FDFAF6", paper_bgcolor="#FDFAF6",
                           font=dict(family="Nunito", color="#5C3D2E"))
        st.plotly_chart(fig2, use_container_width=True)



    st.divider()

    # ── Topic Summary Table 
    st.subheader("Topic Summary")

    summary_rows = []
    for tid, label in TOPIC_LABELS.items():
        subset = df_view[df_view["topic"] == tid]
        if len(subset) == 0:
            continue
        vc = subset["sentiment"].value_counts()
        n  = len(subset)
        summary_rows.append({
            "topic":       label,
            "reviews":     n,
            "positive %":  f"{vc.get('positive', 0) / n * 100:.1f}%",
            "neutral %":   f"{vc.get('neutral',  0) / n * 100:.1f}%",
            "negative %":  f"{vc.get('negative', 0) / n * 100:.1f}%",
        })
    render_topic_cards(summary_rows)

    st.divider()

    # ── Sample Reviews 
    st.subheader("Sample Reviews")
    st.caption("pick a pigeonhole to read what players actually wrote ˘ᵕ˘")
    available_labels = sorted(df_view["topic_label"].unique().tolist())
    selected_label   = st.selectbox("topic", available_labels, label_visibility="collapsed")
    selected_tid     = next((k for k, v in TOPIC_LABELS.items() if v == selected_label), None)

    if selected_tid is not None:
        samples = (
            df_view[df_view["topic"] == selected_tid]
            .sort_values("probability", ascending=False)
            .head(8)
            .reset_index(drop=True)
        )
        render_review_cards(samples)

    st.divider()

    # ── Downloads 
    st.subheader("take your mail home ♡")
    dl1, dl2 = st.columns(2)

    # CSV
    out_cols = ["content", "score", "sentiment", "probability", "topic", "topic_label"]

    csv_out = df_all_view[out_cols].to_csv(index=False)

    with dl1:
        st.download_button(
            label="Download CSV",
            data=csv_out,
            file_name="cozy_analysis_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("all reviews with topics, sentiments, and confidence scores")

    # PDF
    with dl2:
        # generate once and cache in session state
        if "pdf_bytes" not in st.session_state:
            with st.spinner("wrapping up the report... ˘ᵕ˘"):
                try:
                    st.session_state["pdf_bytes"] = generate_pdf(
                        df_all_view, df_view,
                        summary_rows,
                    )
                except Exception as e:
                    st.session_state["pdf_bytes"] = None
                    st.warning(f"PDF generation needs fpdf2 — run `pip install fpdf2` to enable it. ({e})")

        pdf_bytes = st.session_state.get("pdf_bytes")
        if pdf_bytes is not None:
            st.download_button(
                label="Download PDF report",
                data=pdf_bytes,
                file_name="cozy_analysis_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.caption("summary report with topic breakdown and sample reviews")

# ─────────────────────────────────────────────
# UI — About (footer)
# ─────────────────────────────────────────────
st.divider()
with st.expander("About this app"):
    st.markdown(
        "This app uses **BERTopic** to perform topic modeling and sentiment "
        "exploration on user reviews of cozy mobile games from the Google Play "
        "Store. Reviews are grouped into topics based on semantic similarity, "
        "and each is paired with a sentiment label derived from its star rating. "
        "The underlying model was trained and evaluated on reviews from 8 cozy "
        "games spanning farming/life simulation, fantasy adventure, idle "
        "simulation, and management simulation genres, as part of an undergraduate "
        "thesis project. The model result is coherence evaluated at 0.59 and diversity at 0.91 "
    )