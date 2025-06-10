import streamlit as st

st.set_page_config(layout="centered")

from streamlit_extras.stylable_container import stylable_container
from utilities.auth import is_logged_in, logout_button, open_login_page


# -----------------------------
# Reusable Page Functions
# -----------------------------
def cta_button(key: str):
    if is_logged_in():
        logout_button(key=key)
    else:
        open_login_page(key=key)


# -----------------------------
# App Title & Tagline
# -----------------------------
_, contact, signin = st.columns([6, 1.25, 1])

with _:
    st.title("Family Finance App")
with contact:
    st.write(" ")
    st.write(" ")
    with st.popover("Contact"):
        st.markdown("### 📬 Contact Info")
        st.markdown("**Email:** [you@example.com](mailto:you@example.com)")
        st.markdown(
            "**GitHub:** [github.com/yourusername/networth-tracker](https://github.com/yourusername/networth-tracker)"
        )
        st.markdown("**How to Use:**")
        st.markdown(
            """
        1. Fork the [GitHub repo](https://github.com/yourusername/networth-tracker).
        2. Clone it locally or deploy on Streamlit Cloud.
        3. Add your own `secrets.toml` with login credentials.
        4. Customize with your own Google Sheet and account structure.
        """
        )
with signin:
    st.write(" ")
    st.write(" ")
    cta_button(key="signin-title")

st.markdown(
    "###### A cloud-hosted, self-directed finance app built in Streamlit to help you keep tabs on your money—anytime, anywhere."
)
st.write("---")


# -----------------------------
# Section Block Builder
# -----------------------------
def feature_section(
    image_url: str, title: str, description: str, layout: str, key: str
):
    if layout == "left-image":
        img_col, _, txt_col = st.columns([2.25, 0.25, 3])
    else:
        txt_col, _, img_col = st.columns([3, 0.25, 2.5])

    with img_col:
        st.image(image_url)

    with txt_col:
        st.markdown(f"#### {title}")
        st.write(description)
        # cta_button(key)


# -----------------------------
# Sections
# -----------------------------

feature_section(
    image_url="https://cdn.sanity.io/images/mdewiujj/production/7763fb002fce170db0249278bdb8d5e6bfca14c9-3200x2192.png?auto=format&fit=max&q=90&w=3200",
    title="Visualize the Flow of Money",
    description=(
        "Dive deep into your finances with customizable charts that reveal where your money’s going. "
        "Whether you're tracking spending trends, income, or net worth over time, reports help you turn raw data into insights you can act on."
    ),
    layout="left-image",
    key="visualize_flow",
)

st.write("")  # Add vertical spacing

feature_section(
    image_url="https://cdn.sanity.io/images/mdewiujj/production/99dbd52607deac3978603f7ed95e777f425bd5b0-1284x1202.png?auto=format&fit=max&q=90&w=1284",
    title="All Your Accounts in One Place",
    description=(
        "Track all your accounts to see your entire financial picture in one place. "
        "You’ll get a shared view of your finances—making it easier to stay aligned and plan together."
    ),
    layout="right-image",
    key="all_accounts",
)

st.write("")  # Add vertical spacing

feature_section(
    image_url="https://cdn.sanity.io/images/mdewiujj/production/ac4492258662072fc45e5638f21ac55e42199e1e-1689x1188.png?auto=format&fit=max&q=90&w=1689",
    title="Track Your Spending",
    description=(
        "Bring all your transactions into one clean, searchable list—no more jumping between apps or bank websites. "
        "You can stay on top of your spending and quickly spot any unexpected trends."
    ),
    layout="left-image",
    key="track_spending",
)

st.write("\n")  # Add vertical spacing
st.write("---")  # Add vertical spacing
st.write("\n")  # Add vertical spacing

# -----------------------------
# Footer
# -----------------------------
with stylable_container(
    key="my_container",
    css_styles="""
        {
            background-color: #ecebe3;
            padding: 1rem;
            border-radius: 0.5rem;
            border-width: 1px;
            border-style: solid;
            border-color: #3d3a2a;
        }
    """,
):
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("##### 📬 **Contact**")
        st.markdown(
            """
                    - [Feel Free to Email Me!](mailto:benjaminrhoyle@gmail.com)
                    - [GitHub Repository](https://github.com/br-hoyle/networth-tracker-app)
        """
        )

    with col2:
        st.markdown("##### 🔗 **Links**")
        st.markdown(
            """
        - [How to Fork the Repo](https://github.com/br-hoyle/networth-tracker-app#readme)
        - [Streamlit](https://streamlit.io)
        - [Google Sheets API Setup](https://developers.google.com/sheets/api/quickstart/python)
        """
        )
    st.write(" ")

st.markdown("---")
st.caption(
    "🚫 Not financial advice. This tool is for personal tracking only. Consult a qualified human for actual decisions. Use at your own risk—especially if you're terrible with spreadsheets."
)
