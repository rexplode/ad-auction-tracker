
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF
import string

# Caption for the version
st.caption("🆕 Version: Final Build with Google Sheets + Persistent Bids + UI Enhancements")

# Set Streamlit page configuration
st.set_page_config(page_title="Ad Auction Tool", layout="wide")
st.title("📢 Ad Auction Tracker")

# Define Google Sheets scope and connection
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
gc = gspread.authorize(credentials)

# Load spreadsheet and worksheets
sheet = gc.open("Ad Auction Database")
placements_ws = sheet.worksheet("Placements")
bids_ws = sheet.worksheet("Vendor Bids")
delivery_ws = sheet.worksheet("Daily Delivery")
summary_ws = sheet.worksheet("Summary")

# Fetch existing data
placements_df = pd.DataFrame(placements_ws.get_all_records())
bids_df = pd.DataFrame(bids_ws.get_all_records())

# Utility functions
def generate_placement_id():
    existing_ids = placements_df["Placement ID"].tolist()
    existing_numbers = [int(pid[1:]) for pid in existing_ids if pid.startswith("P")]
    next_number = max(existing_numbers, default=0) + 1
    return f"P{next_number:03d}"

def save_placement(data):
    placements_ws.append_row(data)

def update_bids_df(df):
    bids_ws.clear()
    bids_ws.update([df.columns.values.tolist()] + df.values.tolist())

# Session state initialization
if "vendor_colors" not in st.session_state:
    base_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
    vendors = bids_df["Vendor"].unique()
    st.session_state["vendor_colors"] = {vendor: base_colors[i % len(base_colors)] for i, vendor in enumerate(vendors)}

# Tabs
tab1, tab2 = st.tabs(["📋 Auction Builder", "📊 Vendor Reports"])

# Auction Builder
with tab1:
    st.header("📌 Add Ad Placement")
    with st.form("placement_form"):
        placement_id = generate_placement_id()
        name = st.text_input("Placement Name")
        url = st.text_input("Targeted URL")
        tags = st.text_input("Targeting Tags (comma-separated)")
        submit = st.form_submit_button("Add Placement")
        if submit and name:
            save_placement([placement_id, name, url, tags])
            st.success(f"Placement {placement_id} added.")

    st.divider()
    st.header("💰 Vendor Bids")
    edited_df = st.data_editor(bids_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Save Bids"):
        update_bids_df(edited_df)
        st.success("Vendor bids saved and updated!")

# Reporting Tab
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

    for vendor in bids_df["Vendor"].unique():
        with st.expander(f"📦 {vendor}"):
            color = st.session_state["vendor_colors"].get(vendor, "#1f77b4")
            vendor_data = bids_df[bids_df["Vendor"] == vendor]
            st.dataframe(vendor_data)
            fig, ax = plt.subplots()
            vendor_data["Spend"] = vendor_data["Spend"].astype(float)
            vendor_data.groupby("Placement")["Spend"].sum().plot(kind="bar", ax=ax, color=color)
            ax.set_title(f"{vendor} Spend by Placement")
            st.pyplot(fig)

