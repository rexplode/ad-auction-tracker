
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="Ad Auction Tool", layout="wide")
st.caption("🆕 Version: Final Build (Local State Only, No Google Sheets)")
st.title("📢 Ad Auction Tracker")

# Initialize session state
if "placements" not in st.session_state:
    st.session_state["placements"] = []

if "bids" not in st.session_state:
    st.session_state["bids"] = []

# Utility for placement ID
def generate_placement_id():
    return f"P{len(st.session_state['placements']) + 1:03d}"

# Tabs
tab1, tab2 = st.tabs(["📋 Auction Builder", "📊 Vendor Reports"])

with tab1:
    st.header("📌 Add Ad Placement")
    with st.form("placement_form"):
        name = st.text_input("Placement Name")
        url = st.text_input("Targeted URL")
        tags = st.text_input("Targeting Tags (comma-separated)")
        submit = st.form_submit_button("Add Placement")
        if submit and name:
            pid = generate_placement_id()
            st.session_state["placements"].append({
                "Placement ID": pid,
                "Name": name,
                "URL": url,
                "Tags": tags
            })
            st.success(f"Placement {pid} added.")

    st.divider()
    st.header("💰 Vendor Bids")
    bids_df = pd.DataFrame(st.session_state["bids"])
    edited_df = st.data_editor(bids_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Save Bids"):
        st.session_state["bids"] = edited_df.to_dict("records")
        st.success("Vendor bids saved!")

with tab2:
    st.header("📊 Vendor Reports")
    st.sidebar.header("📅 Date Range")
    preset = st.sidebar.radio("Select Range", ["This Week", "Last Week", "Last Month", "Custom"])
    today = datetime.today()

    if preset == "This Week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif preset == "Last Week":
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = start_date + timedelta(days=6)
    elif preset == "Last Month":
        start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        end_date = today.replace(day=1) - timedelta(days=1)
    else:
        start_date = st.sidebar.date_input("Start Date", today - timedelta(days=7))
        end_date = st.sidebar.date_input("End Date", today)

    if st.session_state["bids"]:
        bids_df = pd.DataFrame(st.session_state["bids"])
        for vendor in bids_df["Vendor"].unique():
            with st.expander(f"📦 {vendor}"):
                vendor_data = bids_df[bids_df["Vendor"] == vendor]
                st.dataframe(vendor_data)
                if "Spend" in vendor_data.columns:
                    vendor_data["Spend"] = pd.to_numeric(vendor_data["Spend"], errors="coerce").fillna(0)
                    fig, ax = plt.subplots()
                    vendor_data.groupby("Placement")["Spend"].sum().plot(kind="bar", ax=ax)
                    ax.set_title(f"{vendor} Spend by Placement")
                    st.pyplot(fig)
