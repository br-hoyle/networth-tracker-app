import streamlit as st
from utilities.auth import *

# Non-Authentication Pages
no_auth_pages = {"": [st.Page("pages/home/home.py", title="Home")]}

# Authentication Pages
auth_pages = {
    "Product": [
        st.Page("pages/dashboard/dashboard.py", title="Product Dashboard"),
        # st.Page(
        #     "pages/income_and_expenses/income_and_expenses.py",
        #     title="Income & Expenses",
        # ),
    ],
}

# Only show authentication pages if the user is logged in
if is_logged_in():
    pages = {**no_auth_pages, **auth_pages}
else:
    pages = no_auth_pages

# Navigation Setup
pg = st.navigation(pages, position="sidebar", expanded=True)
pg.run()
