import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Resume ↔ Job Matcher", layout="wide")
st.title("🎯 Resume ↔ Job Matcher (Germany/EU)")

# Resume analysis section
st.subheader("1️⃣ Upload & Analyze Resume")
resume_upload = st.file_uploader("Upload resume (PDF/DOCX/TXT)", type=["pdf","docx","txt"])

if resume_upload and st.button("Analyze Resume", type="secondary"):
    with st.spinner("Analyzing resume..."):
        files = {"resume_upload": (resume_upload.name, resume_upload.getvalue(), resume_upload.type)}
        r = requests.post(f"{BACKEND_URL}/analyze-resume", files=files, timeout=60)
        
        if r.ok:
            analysis = r.json()
            st.success("✅ Resume analyzed successfully!")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Experience Level", analysis["experience_level"])
            with col_b:
                st.metric("Years of Experience", analysis["years_of_experience"] or "N/A")
            with col_c:
                st.metric("Skills Detected", analysis["skill_count"])
            
            with st.expander("📋 Detected Skills", expanded=True):
                st.write(", ".join(analysis["skills"][:30]))
                if analysis["skill_count"] > 30:
                    st.caption(f"...and {analysis['skill_count'] - 30} more")
        else:
            st.error(f"Error analyzing resume: {r.status_code}")
            try:
                st.json(r.json())
            except:
                st.text(r.text)

st.divider()

# Job search section
st.subheader("2️⃣ Search for Jobs")

col1, col2 = st.columns([1,1])

with col1:
    job_title = st.text_input(
        "Job Title", 
        value="", 
        placeholder="e.g., Data Scientist, Software Engineer",
        help="Use broader terms for more results (e.g., 'engineer' instead of 'senior backend engineer')"
    )
    city = st.text_input("City (optional)", value="", placeholder="e.g., Berlin, Munich")
    language = st.selectbox(
        "Language requirement",
        ["Any", "English", "German"] )
    st.caption("⚠️ Language detection is best-effort — jobs with short descriptions may show as 'Unspecified' even if German is required.")
    experience_level = st.selectbox(
        "Experience level (optional)",
        ["Any", "Entry", "Mid", "Senior", "Lead"],
        help="Filter jobs by experience level. 'Any' shows all levels."
    )
    date_posted = st.selectbox(
        "Date posted",
        ["Any time", "Past month", "Past week", "Past 24 hours"]
    )

with col2:
    work_mode = st.radio("Work mode", ["Any", "Remote", "On-site"], horizontal=True)
    country = st.selectbox("Country", ["de"], format_func=lambda x: "Germany")
    pages = st.slider("Pages to fetch", 1, 5, 2)
    results_per_page = st.slider("Results per page", 10, 50, 50)

if st.button("🔍 Find Matching Jobs", type="primary"):
    if not resume_upload:
        st.error("Please upload your resume first.")
    elif not job_title:
        st.error("Please enter a job title.")
    else:
        with st.spinner("🔄 Fetching and analyzing jobs..."):
            files = {"resume_upload": (resume_upload.name, resume_upload.getvalue(), resume_upload.type)}
            data = {
                "job_title": job_title,
                "country": country,
                "city": city or None,
                "pages": pages,
                "results_per_page": results_per_page,
                "work_mode": work_mode,
                "language": language,
                "experience_level": experience_level,
                "date_posted": date_posted,
            }
            r = requests.post(f"{BACKEND_URL}/match", files=files, data=data, timeout=120)
            
            if not r.ok:
                st.error(f"Backend error {r.status_code}")
                try:
                    st.json(r.json())
                except Exception:
                    st.text(r.text)
                st.stop()
            
            matches = r.json()

        if not matches:
            st.warning("⚠️ No matching jobs found.")
            st.info("""
            **Tips to get more results:**
            - Use broader search terms (e.g., "engineer" instead of "senior backend engineer")
            - Try "Any" for language and experience level filters
            - Remove city filter to search nationwide
            - Try different job titles (e.g., "developer", "analyst", "engineer")
            """)
            st.stop()

        st.success(f"✅ Found {len(matches)} matching jobs!")
        
        # Summary metrics
        col_x, col_y, col_z = st.columns(3)
        with col_x:
            avg_score = sum(m['match_percentage'] for m in matches) / len(matches)
            st.metric("Average Match", f"{avg_score:.1f}%")
        with col_y:
            remote_count = sum(1 for m in matches if m['remote_like'])
            st.metric("Remote Jobs", f"{remote_count}/{len(matches)}")
        with col_z:
            st.metric("Sources", len(set(m.get('source','') for m in matches)))
        
        st.divider()
        
        # Display results
        for i, m in enumerate(matches[:25], 1):
            with st.container():
                st.markdown(f"### {i}. {m['title']}")
                st.markdown(f"**{m['company']}** • {m['location']}")
                
                # Metrics row
                col_1, col_2, col_3, col_4, col_5 = st.columns(5)
                with col_1:
                    score_color = "🟢" if m['match_percentage'] >= 70 else "🟡" if m['match_percentage'] >= 50 else "🔴"
                    st.write(f"{score_color} **{m['match_percentage']:.1f}%** match")
                with col_2:
                    st.write(f"📊 **{m.get('experience_level', 'N/A')}**")
                with col_3:
                    st.write(f"🏢 **{m.get('source', 'N/A')}**")
                with col_4:
                    remote_icon = "🏠" if m['remote_like'] else "🏢"
                    st.write(f"{remote_icon} **{'Remote' if m['remote_like'] else 'On-site'}**")
                with col_5:
                    st.write(f"🌍 **{m.get('language_tag', 'N/A')}**")
                
                # Skills
                if m.get("matched_skills"):
                    with st.expander(f"✅ Matched Skills ({len(m['matched_skills'])})", expanded=False):
                        st.write(", ".join(m['matched_skills']))
                
                if m.get("missing_skills"):
                    with st.expander(f"📚 Skills to Develop ({len(m['missing_skills'])})", expanded=False):
                        st.write(", ".join(m['missing_skills']))
                        st.caption("These skills appear in the job description but not in your resume")
                
                # Apply button
                if m.get("url"):
                    st.link_button("🔗 View Job", m["url"], use_container_width=False)
                
                st.divider()
