import streamlit as st


def render_login_page(auth_service):
    st.subheader("Login")

    with st.form("login_form"):
        username = st.text_input("ELMS Username / Student ID")
        password = st.text_input("ELMS Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if not username.strip() or not password.strip():
            st.error("Please enter both username and password.")
            return False
        loading = st.empty()
        loading.markdown(
            '<div class="loading-orb"></div><div class="loading-copy">'
            "Signing you in securely. Please wait...</div>",
            unsafe_allow_html=True,
        )
        with st.status("Connecting securely to ELMS...", expanded=True) as login_status:
            ok = auth_service.login(username.strip(), password)
            login_status.update(
                label="Authentication complete." if ok else "Authentication could not be completed.",
                state="complete" if ok else "error",
                expanded=False,
            )
        loading.empty()
        if ok:
            st.success("Login successful.")
            return True
        st.error(auth_service.last_error or "Authentication failed.")

    st.info("Credentials are never stored in files or logs.")
    return False
