import streamlit as st
from PIL import Image
from openai import OpenAI
import json
import PyPDF2

st.set_page_config(
    page_title="AI Study Note Helper",
    page_icon="📘",
    layout="wide"
)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.markdown(
    "<h1 style='color:#4B0082;'>AI Study Note Helper</h1>",
    unsafe_allow_html=True
)

st.write(
    "Upload or type your messy notes. This app will turn them into a summary, key points, and quiz questions."
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    notes = st.text_area(
        "Paste your notes here:",
        height=280,
        placeholder="Paste class notes, textbook notes, or review materials here..."
    )

with col2:
    uploaded_doc = st.file_uploader(
        "Upload document (PDF/TXT)",
        type=["pdf", "txt"]
    )

    uploaded_image = st.file_uploader(
        "Upload image (optional preview only)",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Image Preview", use_container_width=True)
        st.info("Image preview is supported, but OCR is not included in this version.")

generate = st.button("Generate Study Materials")

if generate:
    final_notes = ""

    if notes.strip():
        final_notes = notes.strip()

    elif uploaded_doc is not None:
        if uploaded_doc.type == "text/plain":
            final_notes = uploaded_doc.read().decode("utf-8")

        elif uploaded_doc.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_doc)
            text = ""

            for page in pdf_reader.pages:
                text += page.extract_text() or ""

            final_notes = text.strip()

    else:
        st.warning("Please paste notes or upload a PDF/TXT document.")
        st.stop()

    if len(final_notes) < 30:
        st.warning("Please provide more detailed notes before generating study materials.")
        st.stop()

    system_prompt = """
You are an AI study assistant designed specifically for high school students.

Only use the information provided by the user.
Do not add outside information.
Make the explanation easy to understand.
Return ONLY valid JSON.

The JSON must follow this exact format:
{
  "Summary": "...",
  "Key Points": ["...", "..."],
  "Quiz": [
    {
      "Question": "...",
      "Choices": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "Answer": "A",
      "Explanation": "..."
    }
  ]
}

Rules:
- Summary should be short and clear.
- Key Points should depend on note length.
- Short notes should have 3-6 key points.
- Long notes should have 7-9 key points.
- Generate 3-5 multiple-choice questions.
- Each quiz question must have exactly 4 choices.
"""

    user_prompt = f"""
Here are my notes:

{final_notes}

Turn them into structured study materials.
"""

    with st.spinner("Generating study materials..."):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

    result_text = response.choices[0].message.content

    try:
        result = json.loads(result_text)

        st.success("Study materials generated!")

        st.subheader("Summary")
        st.write(result.get("Summary", "No summary generated."))

        st.subheader("Key Points")
        for i, point in enumerate(result.get("Key Points", []), start=1):
            st.write(f"{i}. {point}")

        st.subheader("Quiz")
        for i, q in enumerate(result.get("Quiz", []), start=1):
            st.markdown(f"**Question {i}: {q.get('Question', '')}**")

            for choice in q.get("Choices", []):
                st.write(choice)

            st.write(f"**Answer:** {q.get('Answer', '')}")
            st.write(f"**Explanation:** {q.get('Explanation', '')}")
            st.divider()

    except json.JSONDecodeError:
        st.error("The AI response was not valid JSON.")
        st.write(result_text)