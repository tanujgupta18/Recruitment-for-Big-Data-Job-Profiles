
import requests
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Big Data Recruiting", layout="wide")
st.title("🔎 Big Data Talent Recommender")

api_base = st.sidebar.text_input("API Base URL", value="http://localhost:8000")

st.sidebar.header("Quick Actions")
with st.sidebar.expander("Add Resume"):
    name = st.text_input("Name")
    loc = st.text_input("Location")
    exp = st.number_input("Years Experience", min_value=0, value=3)
    skills = st.text_area("Skills (comma separated)")
    summary = st.text_area("Summary")
    if st.button("Submit Resume"):
        r = requests.post(f"{api_base}/resumes", json={
            "name": name, "location": loc, "years_experience": exp,
            "skills": skills, "summary": summary
        })
        st.success(f"Resume added: {r.json()}")

with st.sidebar.expander("Add Job"):
    title = st.text_input("Job Title", value="Senior Data Engineer")
    jloc = st.text_input("Job Location", value="Bengaluru")
    min_exp = st.number_input("Min Exp", min_value=0, value=5)
    desc = st.text_area("Job Description", value="Spark, Kafka, AWS, streaming pipelines, Scala")
    if st.button("Submit Job"):
        r = requests.post(f"{api_base}/jobs", json={
            "title": title, "location": jloc, "min_exp": int(min_exp), "description": desc
        })
        st.success(f"Job added: {r.json()}")

st.header("Find Candidates")
jd = st.text_area("Paste Job Description", value="Looking for Spark, Kafka, AWS, streaming pipelines, Scala preferred")
col1, col2, col3 = st.columns(3)
with col1:
    floc = st.text_input("Filter by Location (optional)", value="")
with col2:
    fexp = st.number_input("Min Experience (optional)", min_value=0, value=0)
with col3:
    topk = st.slider("Top K", 1, 20, 10)

if st.button("Recommend"):
    payload = {
        "description": jd,
        "top_k": topk,
        "location": floc if floc.strip() else None,
        "min_exp": int(fexp) if fexp>0 else None
    }
    r = requests.post(f"{api_base}/recommend", json=payload)
    data = r.json()["results"]
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"), "matches.csv")
    else:
        st.warning("No matching candidates found.")
