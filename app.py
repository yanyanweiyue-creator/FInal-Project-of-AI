# AI Study Note Helper App
# This app is designed for students who want to turn messy or unorganized study notes into structured learning materials.
# Users can input notes by typing directly or uploading a PDF/TXT file containing their notes.
# The app uses an AI model to generate:
# Key Points — a clear list of important ideas from the notes
# Quiz Questions — either MCQ (with answers and explanations) or FRQ (with sample answers and rubric)
# The generated results are displayed in the app, and users can interact with the quiz and check their answers.
# Expected input: raw study notes from any subject (e.g., AP classes, lecture notes, textbook summaries).


import streamlit as st
from PIL import Image
from openai import OpenAI
import json
import st_yled
import PyPDF2



# I do not know why my API KEY cannot work when I use Client = OpenAi(api_key=st.secrets["OPENAI_API_KEY"]), so I ask AI to figuer out how to solve that.

st.set_page_config(page_title="AI Study Note Helper", page_icon="📘", layout="wide")

st_yled.init()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.markdown("<h1 style='color:#4B0082;'>AI Study Note Helper</h1>", unsafe_allow_html=True)
st_yled.text("Paste notes or upload a file. The app will turn them into key points or quiz.")
if "page" not in st.session_state:
    st.session_state["page"] = "home"
st.divider()

if st.session_state["page"] == "home":


    col1, col2 = st.columns(2)
    with st_yled.container(
        background_color="#121212",
        padding=20,
    ):
        with col1:
            notes = st_yled.text_area("Your notes:", height=210)

        with col2:
            file = st_yled.file_uploader("Upload PDF/TXT", type=["pdf", "txt"])
            img = st_yled.file_uploader("Image (preview only)", type=["png", "jpg", "jpeg"])

            if img:
                st.image(Image.open(img), use_container_width=True)

    task = st_yled.radio(
        "What do you want to generate?",
        ["Key Points", "Quiz"]
    )

    if task == "Key Points":
        point_num = st_yled.number_input("Number of Key Points", 1, 10, 5)
        generate_button = st_yled.button("Generate Key Points")

    else:
        quiz_type = st_yled.radio("Quiz Type", ["MCQ", "FRQ"])
        quiz_num = st_yled.number_input("Number of questions", 1, 10, 3)
        generate_button = st_yled.button("Generate Quiz")

    text = ""

    # From AI since I do not know how to let AI read file in streamlit, so I just put it here.
    if notes.strip():
        text = notes
    elif file:
        if file.type == "text/plain":
            text = file.read().decode("utf-8")

        elif file.type == "application/pdf":
            reader = PyPDF2.PdfReader(file)
            for p in reader.pages:
                text += p.extract_text() or ""


    if generate_button:
        
        if not text:
            st_yled.warning("Please add some notes first.")

        else:
            if task == "Key Points":
                system_prompt = f"""
                You are a study assistant.
                Only use given notes.
                Return JSON only.

                Format:
                {{
                "Key Points": ["...", "...", "..."]
                }}

                Rule:
                The total number of key points must be exactly {point_num}.
                """

            else:
                system_prompt = f"""
                You are a study assistant.
                Only use given notes.
                Return JSON only.

                Quiz type: {quiz_type}
                Number of questions: {quiz_num}

                If MCQ, return:
                {{
                "Quiz": [
                    {{
                    "Question": "...",
                    "Choices": ["A. ...", "B. ...", "C. ...", "D. ..."],
                    "Answer": "A",
                    "Explanation": "..."
                    }}
                ]
                }}

                If FRQ, return:
                {{
                "Quiz": [
                    {{
                    "Question": "...",
                    "Sample Answer": "...",
                    "Rubric": ["...", "...", "..."]
                    }}
                ]
                }}

                Make exactly {quiz_num} questions.
                """

            user_prompt = f"Notes: {text}"

            with st_yled.spinner("Generating..."):
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )

            mamba = res.choices[0].message.content

            try:
                data = json.loads(mamba)

            except:
                st_yled.error("Error reading response")
                st_yled.text(mamba)

            else:
                if task == "Key Points":
                    st.session_state["key_points_data"] = data
                    st.session_state["quiz_data"] = None
                else:
                    st.session_state["quiz_data"] = data
                    st.session_state["quiz_type"] = quiz_type
                    st.session_state["key_points_data"] = None

                st.session_state["page"] = "output"
                st.rerun()


if st.session_state["page"] == "output":
    with st.container():
        st.markdown(
            """
            <style>
            .stContainer {
                background-color: black;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 15px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        if st.session_state.get("key_points_data"):
            data = st.session_state["key_points_data"]

            st.subheader("Key Points")

            for i, p in enumerate(data.get("Key Points", []), 1):
                st_yled.text(f"{i}. {p}")


        if st.session_state.get("quiz_data"):
            data = st.session_state["quiz_data"]
            saved_quiz_type = st.session_state.get("quiz_type", "MCQ")

            st.subheader("Quiz")

            if saved_quiz_type == "MCQ":
                for i, q in enumerate(data.get("Quiz", []), 1):
                    st.markdown(f"**Q{i}: {q.get('Question', '')}**")

                    for c in q.get("Choices", []):
                        st_yled.text(c)

                    st_yled.radio(
                        "Choose:",
                        ["A", "B", "C", "D"],
                        key=f"ans_{i}"
                    )

                    st.divider()

                if st_yled.button("Check"):
                    score = 0
                    total = len(data.get("Quiz", []))
            
                    for i, q in enumerate(data.get("Quiz", []), 1):
                        user = st.session_state.get(f"ans_{i}", "")
                        correct = q.get("Answer", "")

                        if user == correct:
                            st_yled.success(f"Q{i}: Correct")
                            score += 1
                        else:
                            st_yled.error(f"Q{i}: Wrong. Correct answer: {correct}")

                        st_yled.text(f"Explanation: {q.get('Explanation', '')}")

                    st.subheader(f"Score: {score}/{total}")

            else:
                for i, q in enumerate(data.get("Quiz", []), 1):
                    st.markdown(f"**Q{i}: {q.get('Question', '')}**")

                    st_yled.text_area(
                        "Your answer:",
                        key=f"frq_{i}"
                    )

                    st_yled.divider()

                if st_yled.button("Check"):
                    for i, q in enumerate(data.get("Quiz", []), 1):
                        st.markdown(f"Q{i} Sample Answer:")
                        st_yled.text(q.get("Sample Answer", ""))

                        st_yled.text("Rubric:")
                        for r in q.get("Rubric", []):
                            st_yled.text(f"- {r}")

                        st.divider()
    
    if st_yled.button("Back"):
        st.session_state["page"] = "home"
        st.rerun()