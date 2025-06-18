import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from utilities.gsheets import *
from utilities.auth import logout_button

conn = st.connection("gsheets", type=GSheetsConnection)


def show_app_sidebar():
    with st.sidebar:

        view_type = st.segmented_control(
            "**View**",
            options=["Dashboard", "Spreadsheet"],
            key="nav",
            selection_mode="single",
            default=["Dashboard"],
        )

        # Balances
        st.markdown("##### Balances")

        if st.button(
            type="primary",
            use_container_width=True,
            label="Add Balances",
            key="add_balance_button_control",
        ):
            add_balance_records(conn=conn)

        balance_columns = st.columns(2)
        with balance_columns[0]:
            edit_balance_records(conn=conn)

        with balance_columns[1]:
            delete_balance_records(conn=conn)

        # Transactions
        st.markdown("##### Transaction")

        if st.button(
            type="primary",
            use_container_width=True,
            label="Add Transactions",
            key="add_transaction_button_control",
        ):
            st.write("Add transactions")

        transaction_columns = st.columns(2)
        with transaction_columns[0]:
            edit_transaction_records(conn=conn)

        with transaction_columns[1]:
            delete_transaction_records(conn=conn)

        # Logout
        logout_button(key="sidebar_logout")

        return view_type
