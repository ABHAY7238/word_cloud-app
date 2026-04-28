import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from io import BytesIO
import base64
import PyPDF2
from docx import Document
import re

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="Advanced Word Cloud Generator",
    layout="wide"
)

st.title("☁️ Advanced Word Cloud Generator")

# -----------------------------
# FILE READERS (CACHED)
# -----------------------------
@st.cache_data(show_spinner=False)
def read_txt(file):
    return file.getvalue().decode("utf-8", errors="ignore")

@st.cache_data(show_spinner=False)
def read_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

@st.cache_data(show_spinner=False)
def read_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return " ".join([page.extract_text() or "" for page in pdf.pages])

# -----------------------------
# TEXT CLEANING PIPELINE
# -----------------------------
def clean_text(text, lowercase=True, remove_punctuation=True):
    if lowercase:
        text = text.lower()
    if remove_punctuation:
        text = re.sub(r"[^\w\s]", "", text)
    return text

def remove_stopwords(text, stopwords_set):
    words = text.split()
    return " ".join([w for w in words if w not in stopwords_set])

def compute_word_freq(text):
    df = pd.DataFrame({'Word': text.split()})
    freq = df.value_counts().reset_index(name='Count')
    return freq.sort_values(by="Count", ascending=False)

# -----------------------------
# DOWNLOAD UTILITIES
# -----------------------------
def download_image(fig, format_, dpi):
    buf = BytesIO()
    fig.savefig(buf, format=format_, dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    href = f'<a href="data:image/{format_};base64,{b64}" download="wordcloud.{format_}">📥 Download Image</a>'
    return href

def download_csv(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="word_count.csv">📥 Download CSV</a>'
    return href

# -----------------------------
# SIDEBAR CONTROLS
# -----------------------------
st.sidebar.header("⚙️ Controls")

use_stopwords = st.sidebar.checkbox("Use default stopwords", True)
custom_stopwords = st.sidebar.text_area("Custom stopwords (comma-separated)")

width = st.sidebar.slider("Width", 400, 2000, 1200)
height = st.sidebar.slider("Height", 200, 2000, 800)
max_words = st.sidebar.slider("Max Words", 50, 500, 200)

colormap = st.sidebar.selectbox(
    "Color Map",
    ["viridis", "plasma", "inferno", "magma", "cividis"]
)

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader("📁 Upload TXT, PDF, or DOCX", type=["txt", "pdf", "docx"])

if uploaded_file:

    # File info
    st.info(f"**File:** {uploaded_file.name} | {uploaded_file.type}")

    # Read file
    if uploaded_file.type == "text/plain":
        text = read_txt(uploaded_file)
    elif uploaded_file.type == "application/pdf":
        text = read_pdf(uploaded_file)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = read_docx(uploaded_file)
    else:
        st.error("Unsupported file type")
        st.stop()

    # -----------------------------
    # PREVIEW
    # -----------------------------
    with st.expander("🔍 Preview Raw Text"):
        st.write(text[:2000] + "..." if len(text) > 2000 else text)

    # -----------------------------
    # PROCESSING
    # -----------------------------
    text = clean_text(text)

    # Stopwords handling
    stopwords = set()
    if use_stopwords:
        stopwords = STOPWORDS

    if custom_stopwords:
        custom = set([w.strip().lower() for w in custom_stopwords.split(",")])
        stopwords = stopwords.union(custom)

    text = remove_stopwords(text, stopwords)

    if not text.strip():
        st.warning("No valid text after processing.")
        st.stop()

    # -----------------------------
    # WORD FREQUENCY
    # -----------------------------
    word_freq = compute_word_freq(text)

    # -----------------------------
    # LAYOUT
    # -----------------------------
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("☁️ Word Cloud")

        fig, ax = plt.subplots(figsize=(width/100, height/100))

        wc = WordCloud(
            width=width,
            height=height,
            background_color="white",
            max_words=max_words,
            colormap=colormap
        ).generate(text)

        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")

        st.pyplot(fig)

        # Download options
        format_ = st.selectbox("Export Format", ["png", "jpeg", "svg", "pdf"])
        dpi = st.slider("Resolution (DPI)", 100, 500, 300)

        st.markdown(download_image(fig, format_, dpi), unsafe_allow_html=True)

    with col2:
        st.subheader("📊 Top Words")
        st.dataframe(word_freq.head(20), use_container_width=True)

        st.markdown(download_csv(word_freq), unsafe_allow_html=True)

    # -----------------------------
    # OPTIONAL: BAR CHART
    # -----------------------------
    st.subheader("📈 Word Frequency Chart")

    top_n = st.slider("Top N words", 5, 50, 15)

    chart_data = word_freq.head(top_n).set_index("Word")

    st.bar_chart(chart_data)

else:
    st.warning("Upload a file to begin.")









