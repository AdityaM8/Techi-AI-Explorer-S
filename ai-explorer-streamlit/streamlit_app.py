import os, json
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:3000").rstrip("/")
API_TOKEN = os.getenv("API_TOKEN", "").strip()

st.set_page_config(page_title="AI Explorer (Streamlit)", layout="wide")

def api(path, method="GET", **kwargs):
    url = f"{API_BASE}{path}"
    headers = kwargs.pop("headers", {})
    headers["Accept"] = "application/json"
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    try:
        r = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    except requests.exceptions.RequestException as e:
        st.error(f"Cannot reach API at {API_BASE}. Error: {e}")
        st.stop()
    if r.status_code >= 400:
        try:
            data = r.json()
        except Exception:
            data = r.text
        st.error(f"API error {r.status_code}: {data}")
        st.stop()
    ctype = r.headers.get("content-type","")
    return r.json() if "application/json" in ctype else r.text

with st.sidebar:
    st.header("AI Explorer — Streamlit")
    st.caption("Frontend client for your Next.js API")
    st.write(f"**API_BASE:** `{API_BASE}`")
    try:
        health = api("/api/health")
        st.success("API reachable ✓")
    except Exception:
        st.error("API not reachable")
    st.divider()
    st.caption("Tip: Use the Sessions tab to continue working on an existing tool.")

st.title("AI Explorer — Streamlit UI")
st.write("State your task → get the best free AI tools → open sessions here.")

# --- Task Intake ---
with st.container(border=True):
    st.subheader("Describe your task")
    task_desc = st.text_area(" ", placeholder="e.g., Write a 500-word blog on AI in healthcare", height=120, key="task_desc")
    col_a, col_b = st.columns([1,3])
    with col_a:
        submit = st.button("Get recommendations", type="primary", use_container_width=True)
    with col_b:
        st.caption("AI Explorer will suggest the best free tools and open them here.")

    if submit:
        if len(task_desc.strip()) < 10:
            st.warning("Please describe your task in more detail (≥ 10 characters).")
        else:
            res = api("/api/tasks", method="POST", json={"description": task_desc})
            st.session_state["task_id"] = res["taskId"]
            st.session_state["active_session"] = None
            st.session_state["last_task_desc"] = task_desc

task_id = st.session_state.get("task_id")

t1, t2 = st.tabs(["Recommendations", "Sessions"])

with t1:
    if not task_id:
        st.info("Enter a task above to see recommendations.")
    else:
        st.caption(f"Task ID: {task_id}")
        recs = api(f"/api/tasks/{task_id}/recommendations")
        if not recs:
            st.warning("No recommendations yet. Try seeding tools in the API.")
        else:
            cols = st.columns(2)
            for i, rec in enumerate(recs):
                c = cols[i % 2]
                tool = rec["tool"]
                with c.container(border=True):
                    st.markdown(f"### {tool['name']}")
                    st.write(f"**Category:** {tool['category']}  \n{rec['rationale']}")
                    embed = "Embeds here ✅" if tool["supportsEmbed"] else "Opens externally ↗"
                    st.caption(embed)
                    if st.button(f"Select & Open: {tool['name']}", key=f"sel_{i}"):
                        payload = {"taskId": task_id, "toolId": tool["id"]}
                        data = api("/api/sessions", method="POST", json=payload)
                        st.session_state["active_session"] = data["sessionId"]
                        st.experimental_rerun()

with t2:
    if not task_id:
        st.info("Create a task first to view sessions.")
    else:
        sessions = api(f"/api/tasks/{task_id}/sessions")
        if not sessions:
            st.info("No sessions yet. Go to Recommendations to select a tool.")
        else:
            sid_to_title = {s["id"]: s["title"] for s in sessions}
            default_sid = st.session_state.get("active_session") or sessions[0]["id"]
            chosen = st.selectbox("Open session", options=list(sid_to_title.keys()),
                                  format_func=lambda x: sid_to_title[x],
                                  index=list(sid_to_title.keys()).index(default_sid))
            st.session_state["active_session"] = chosen

            detail = api(f"/api/sessions/{chosen}")
            left, right = st.columns([1,1])

            with left:
                st.markdown("### Transcript")
                msgs = json.loads(detail["transcript"])
                for m in msgs:
                    role = m.get("role", "assistant")
                    st.markdown(f"**[{role}]** {m.get('content','')}")
                with st.form("send_msg", clear_on_submit=True):
                    user_msg = st.text_input("Message to this agent…")
                    send = st.form_submit_button("Send")
                    if send and user_msg.strip():
                        api(f"/api/sessions/{chosen}", method="POST",
                            json={"role":"user","content":user_msg.strip()})
                        st.experimental_rerun()

            with right:
                st.markdown("### Agent Window")
                tool = detail["tool"]
                if tool["supportsEmbed"]:
                    st.components.v1.iframe(tool["siteUrl"], height=520)
                else:
                    st.info("This tool opens externally due to embedding policy.")
                    st.link_button("Open Tool", url=tool["siteUrl"])
