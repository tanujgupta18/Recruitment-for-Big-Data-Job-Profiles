import streamlit as st
import pandas as pd
from app.matcher.recommend import Matcher

# --- Email deps (new) ---
import smtplib, ssl
from email.message import EmailMessage

# Initialize matcher (loads resumes + jobs CSV)
matcher = Matcher()

# ----------------------------
# EMAIL: helper
# ----------------------------
def send_email_real(to_email: str, subject: str, body_text: str, body_html: str | None = None):
    """
    Sends a real email using Gmail SMTP via App Password.
    Configure credentials in app/.streamlit/secrets.toml
    """
    user = st.secrets["EMAIL_USER"]
    pwd  = st.secrets["EMAIL_PASS"]
    from_hdr = st.secrets.get("EMAIL_FROM", user)
    host = st.secrets.get("SMTP_HOST", "smtp.gmail.com")
    port = int(st.secrets.get("SMTP_PORT", 465))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_hdr
    msg["To"] = to_email
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context) as server:
        server.login(user, pwd)
        server.send_message(msg)

def render_quick_mail_ui(possible_df: pd.DataFrame | None):
    st.markdown("### ✉️ Quick Offer Mail")

    picked_email = ""
    picked_name = ""

    # Try to prefill from recommendations table if present
    if possible_df is not None and not possible_df.empty:
        email_col = next((c for c in possible_df.columns if c.lower() in ("email", "mail", "candidate_email")), None)
        name_col = next((c for c in possible_df.columns if c.lower() in ("name", "full_name", "candidate_name")), None)

        if email_col:
            options = []
            for _, r in possible_df.iterrows():
                nm = (str(r[name_col]).strip() if (name_col and pd.notna(r.get(name_col, ""))) else "").strip()
                em = str(r[email_col]).strip()
                if em:
                    label = f"{nm} <{em}>" if nm else em
                    options.append((label, nm, em))

            if options:
                labels = [o[0] for o in options]
                sel = st.selectbox("Pick from recommendations", labels)
                for lbl, nm, em in options:
                    if lbl == sel:
                        picked_name, picked_email = nm, em
                        break

    # Manual or prefilled inputs
    candidate_email = st.text_input("Recipient email", value=picked_email, placeholder="person@example.com")
    candidate_name = st.text_input("Recipient name (optional)", value=picked_name)

    subject = st.text_input(
        "Subject",
        value="Congratulations — You’re selected for the Big Data role",
    )

    text_body = f"""Hi {candidate_name or 'there'},

Congratulations! Based on our evaluation, you'd be a great fit for our Big Data role.

If you're interested, please reply to this email so we can schedule next steps.

Best,
Recruiting Team
"""

    html_body = f"""
<p>Hi {candidate_name or 'there'},</p>
<p>Congratulations! Based on our evaluation, you'd be a great fit for our <b>Big Data</b> role.</p>
<p>If you're interested, please reply to this email so we can schedule next steps.</p>
<p>Best,<br/>Recruiting Team</p>
"""

    use_html = st.checkbox("Send as HTML", value=True)

    if st.button("Send Email", type="primary", disabled=not candidate_email):
        try:
            send_email_real(
                to_email=candidate_email,
                subject=subject,
                body_text=text_body,
                body_html=html_body if use_html else None,
            )
            st.success(f"✅ Email sent successfully to {candidate_email}")
        except Exception as e:
            st.error(f"❌ Failed to send: {e}")


# ----------------------------
# PAGE SETUP
# ----------------------------
st.set_page_config(page_title="Big Data Recruiting", layout="wide")
st.title("🔎 Big Data Talent Recommender")

st.sidebar.header("Quick Actions")

# ----------------------------
# ADD RESUME SECTION
# ----------------------------
with st.sidebar.expander("Add Resume"):
    name = st.text_input("Name")
    email = st.text_input("Email") 
    loc = st.text_input("Location")
    exp = st.number_input("Years Experience", min_value=0, value=3)
    skills = st.text_area("Skills (comma separated)")
    summary = st.text_area("Summary")
    if st.button("Submit Resume"):
        rec = {
            "name": name,
            "email": email,                        
            "location": loc,
            "years_experience": int(exp),
            "skills": skills,
            "summary": summary
        }
        matcher.add_resume(rec)
        st.success(f"✅ Resume added successfully for {name}!")

# ----------------------------
# ADD JOB SECTION
# ----------------------------
with st.sidebar.expander("Add Job"):
    title = st.text_input("Job Title", value="Senior Data Engineer")
    jloc = st.text_input("Job Location", value="Bengaluru")
    min_exp = st.number_input("Min Exp", min_value=0, value=5)
    desc = st.text_area("Job Description", value="Spark, Kafka, AWS, streaming pipelines, Scala")
    if st.button("Submit Job"):
        rec = {
            "title": title,
            "location": jloc,
            "min_exp": int(min_exp),
            "description": desc
        }
        matcher.add_job(rec)
        st.success(f"✅ Job added successfully: {title}")

# ----------------------------
# FIND MATCHES SECTION
# ----------------------------
st.header("Find Candidates")
jd = st.text_area(
    "Paste Job Description",
    value="Looking for Spark, Kafka, AWS, streaming pipelines, Scala preferred"
)
col1, col2, col3 = st.columns(3)
with col1:
    floc = st.text_input("Filter by Location (optional)", value="")
with col2:
    fexp = st.number_input("Min Experience (optional)", min_value=0, value=0)
with col3:
    topk = st.slider("Top K", 1, 20, 10)

df = None  # will hold recommendations for email UI

if st.button("Recommend"):
    results = matcher.match_for_job(
        description=jd,
        top_k=topk,
        location=floc if floc.strip() else None,
        min_exp=int(fexp) if fexp > 0 else None
    )

    if results:
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        st.download_button(
            "⬇️ Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            "matches.csv"
        )

        # --- Email UI (new) right under the table ---
        render_quick_mail_ui(df)
    else:
        st.warning("⚠️ No matching candidates found.")

# If user hasn't clicked Recommend yet, still allow manual email send
if df is None:
    with st.expander("Send Quick Offer Email (manual)", expanded=False):
        render_quick_mail_ui(None)
