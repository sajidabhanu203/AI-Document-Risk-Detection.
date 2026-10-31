import re
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st
from pypdf import PdfReader
from docx import Document


st.set_page_config(
    page_title="DocuShield | Risk & Compliance",
    page_icon="🛡️",
    layout="wide",
)

# -------------------- Styling --------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f5f3ff 0%, #eef5ff 100%);
    color: #1f2937;
}

.block-container {
    padding-top: 2rem;
    max-width: 1250px;
}

.hero {
    padding: 25px;
    border-radius: 18px;
    color: white !important;
    background: linear-gradient(110deg, #312e81, #6366f1, #2563eb);
    margin-bottom: 22px;
}

.hero h1,
.hero h3,
.hero p {
    color: white !important;
}

h1, h2, h3, h4, p, label {
    color: #1f2937;
}

[data-testid="stMarkdownContainer"] p {
    color: #1f2937;
}

.small-note {
    color: #555875 !important;
    font-size: 13px;
}

[data-testid="stSidebar"] {
    background-color: #f8fafc;
}

div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid #e2e8f0;
    padding: 14px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="hero">
    <h1>🛡️ DocuShield</h1>
    <h3>Document Risk &amp; Compliance Classifier</h3>
    <p>Upload a document, identify potential risk indicators, and review the findings.</p>
</div>
""", unsafe_allow_html=True)


# -------------------- Risk Rules --------------------
RULES = [
    {
        "category": "Data Privacy",
        "severity": "High",
        "patterns": [
            r"\bshare personal data without consent\b",
            r"\bwithout (?:the )?(?:user|customer|individual)'?s consent\b",
            r"\bdisclose personal information without authorization\b",
            r"\bcollect sensitive personal data without consent\b",
        ],
        "reason": "Possible handling or disclosure of personal data without consent.",
    },
    {
        "category": "Security",
        "severity": "High",
        "patterns": [
            r"\bdisable (?:all )?security controls\b",
            r"\bshare passwords\b",
            r"\bunencrypted passwords\b",
            r"\bno authentication required\b",
            r"\bpublicly expose confidential data\b",
        ],
        "reason": "Possible weakness in security or access protection.",
    },
    {
        "category": "Compliance",
        "severity": "High",
        "patterns": [
            r"\bignore applicable regulations\b",
            r"\bavoid regulatory reporting\b",
            r"\bdelete audit logs\b",
            r"\bconceal (?:a )?(?:compliance violation|regulatory breach)\b",
        ],
        "reason": "Wording may indicate avoidance of compliance or audit obligations.",
    },
    {
        "category": "Contractual Risk",
        "severity": "Medium",
        "patterns": [
            r"\bunlimited liability\b",
            r"\bno liability for any damages\b",
            r"\bunilateral(?:ly)? change (?:the )?(?:terms|agreement)\b",
            r"\bterminate without notice\b",
        ],
        "reason": "Potentially important contractual term that may need review.",
    },
    {
        "category": "Data Retention",
        "severity": "Medium",
        "patterns": [
            r"\bretain personal data indefinitely\b",
            r"\bkeep data forever\b",
            r"\bno deletion policy\b",
            r"\bretain data permanently\b",
        ],
        "reason": "Possible issue involving data retention or deletion.",
    },
    {
        "category": "Operational Risk",
        "severity": "Low",
        "patterns": [
            r"\bmanual process without review\b",
            r"\bno backup process\b",
            r"\bno documented procedure\b",
        ],
        "reason": "Potential operational weakness that may need review.",
    },
]


# -------------------- Extract Document Text --------------------
def extract_text(uploaded_file):
    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()

    if name.endswith(".txt"):
        return raw.decode("utf-8", errors="replace")

    if name.endswith(".pdf"):
        reader = PdfReader(BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    if name.endswith(".docx"):
        document = Document(BytesIO(raw))
        paragraphs = [p.text for p in document.paragraphs]
        tables = [
            cell.text
            for table in document.tables
            for row in table.rows
            for cell in row.cells
        ]
        return "\n".join(paragraphs + tables)

    raise ValueError("Unsupported file type.")


def split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    return re.split(r"""(?<=[.!?])\s+(?=[A-Z0-9"'])""", text)


# -------------------- Analyze Document --------------------
def analyze_document(text):
    findings = []
    seen = set()

    for sentence in split_sentences(text):
        for rule in RULES:
            matched = any(
                re.search(pattern, sentence, flags=re.IGNORECASE)
                for pattern in rule["patterns"]
            )

            if matched:
                key = (sentence.lower(), rule["category"])

                if key in seen:
                    continue

                seen.add(key)

                findings.append({
                    "Risk Category": rule["category"],
                    "Risk Level": rule["severity"],
                    "Flagged Text": sentence.strip(),
                    "Reason": rule["reason"],
                    "Review Status": "Needs human review",
                })

    return pd.DataFrame(
        findings,
        columns=[
            "Risk Category",
            "Risk Level",
            "Flagged Text",
            "Reason",
            "Review Status",
        ],
    )


# -------------------- Session State --------------------
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "document_name" not in st.session_state:
    st.session_state.document_name = ""

if "document_text_length" not in st.session_state:
    st.session_state.document_text_length = 0


# -------------------- Sidebar --------------------
with st.sidebar:
    st.header("📁 Document Center")

    uploaded = st.file_uploader(
        "Upload a document",
        type=["pdf", "docx", "txt"],
        help="Text-based PDF files are supported. Scanned PDFs may need OCR.",
    )

    st.markdown("---")
    st.markdown("### Supported files")
    st.write("• PDF")
    st.write("• Word DOCX")
    st.write("• Plain text TXT")

    st.markdown("---")
    st.caption("DocuShield prototype | Rule-based screening")


# -------------------- Main Area --------------------
st.subheader("Document Analysis")

if uploaded is not None:
    st.info(f"Selected document: {uploaded.name}")

    if st.button("🔍 Analyze Document", type="primary"):
        try:
            with st.spinner("Reading and analyzing the document..."):
                document_text = extract_text(uploaded)

                if not document_text.strip():
                    st.warning(
                        "No readable text was found. "
                        "For scanned PDFs, OCR may be required."
                    )
                    st.session_state.analysis_result = None

                else:
                    st.session_state.analysis_result = analyze_document(
                        document_text
                    )
                    st.session_state.document_name = uploaded.name
                    st.session_state.document_text_length = len(document_text)

        except Exception as exc:
            st.error(f"Could not read this file: {exc}")

elif st.session_state.analysis_result is None:
    st.markdown("""
    Upload a PDF, DOCX, or TXT document using the sidebar.

    The application will scan its text for predefined risk indicators.
    """)


# -------------------- Risk Dashboard --------------------
if st.session_state.analysis_result is not None:
    results = st.session_state.analysis_result

    st.markdown("---")
    st.subheader("📊 Risk Dashboard")

    total = len(results)
    high = int((results["Risk Level"] == "High").sum())
    medium = int((results["Risk Level"] == "Medium").sum())
    low = int((results["Risk Level"] == "Low").sum())

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Flagged Findings", total)
    c2.metric("High Risk", high)
    c3.metric("Medium Risk", medium)
    c4.metric("Low Risk", low)

    st.caption(
        f"Document: {st.session_state.document_name} | "
        f"Text characters: {st.session_state.document_text_length:,}"
    )

    if total == 0:
        st.success(
            "No configured risk patterns were detected. "
            "This does not prove the document is risk-free."
        )

    else:
        left, right = st.columns(2)

        with left:
            st.markdown("#### Findings by risk level")

            level_counts = (
                results["Risk Level"]
                .value_counts()
                .reindex(["High", "Medium", "Low"], fill_value=0)
                .rename_axis("Risk Level")
                .reset_index(name="Count")
            )

            fig = px.bar(
                level_counts,
                x="Risk Level",
                y="Count",
                color="Risk Level",
                color_discrete_map={
                    "High": "#dc2626",
                    "Medium": "#f59e0b",
                    "Low": "#16a34a",
                },
            )

            fig.update_layout(
                showlegend=False,
                template="plotly_white",
            )

            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.markdown("#### Findings by category")

            category_counts = (
                results["Risk Category"]
                .value_counts()
                .rename_axis("Category")
                .reset_index(name="Count")
            )

            fig2 = px.pie(
                category_counts,
                names="Category",
                values="Count",
                hole=0.45,
            )

            fig2.update_layout(template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)

    # -------------------- Flagged Clauses --------------------
    st.markdown("---")
    st.subheader("🚩 Flagged Clauses")

    if total:
        chosen_levels = st.multiselect(
            "Filter by risk level",
            ["High", "Medium", "Low"],
            default=["High", "Medium", "Low"],
        )

        filtered = results[
            results["Risk Level"].isin(chosen_levels)
        ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = filtered.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "⬇️ Download Findings as CSV",
            data=csv_data,
            file_name="document_risk_findings.csv",
            mime="text/csv",
        )

        st.markdown("#### Human Review")

        st.warning(
            "These are preliminary rule matches, not verified violations. "
            "Review the full document and applicable policies before making decisions."
        )

    else:
        st.write("There are no flagged clauses to display.")

    if st.button("Clear Analysis"):
        st.session_state.analysis_result = None
        st.session_state.document_name = ""
        st.session_state.document_text_length = 0
        st.rerun()


# -------------------- Footer --------------------
st.markdown("---")

st.markdown(
    """
    <p class="small-note">
    DocuShield is a demonstration tool. It does not provide legal advice
    or certify regulatory compliance. Unmatched text may still contain risks.
    </p>
    """,
    unsafe_allow_html=True,
)