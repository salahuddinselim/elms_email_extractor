from urllib.parse import quote

import streamlit as st


def render_sms_composer() -> None:
    st.subheader("SMS composer")
    st.caption(
        "Prepare a text message after extraction. Phone numbers are entered locally, "
        "and the app opens your device's SMS handler without sending or storing messages."
    )
    recipients = st.text_input(
        "Phone numbers",
        placeholder="+8801XXXXXXXXX, +8801YYYYYYYYY",
        help="Separate multiple numbers with commas or spaces.",
    )
    message = st.text_area(
        "SMS message",
        value="Hello, please check the group invitation or course update shared with you.",
        height=140,
    )
    numbers = [number.strip() for number in recipients.replace(",", " ").split() if number.strip()]
    if not numbers:
        st.info("Enter at least one phone number to prepare the SMS.")
        return

    sms_url = f"sms:{','.join(numbers)}?body={quote(message)}"
    st.caption(f"{len(numbers)} recipient(s) prepared.")
    st.link_button("Open SMS app", sms_url, type="primary")
