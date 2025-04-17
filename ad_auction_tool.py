
import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta

st.set_page_config(page_title="Ad Auction Tool", layout="wide")
st.title("📢 Ad Auction Tracker (MVP)")

# Initialize session state
if "placements" not in st.session_state:
    st.session_state["placements"] = []
if "bids" not in st.session_state:
    st.session_state["bids"] = []

# ---- PLACEMENT FORM ----
st.header("📌 Add Ad Placement")
with st.form("placement_form"):
    placement_id = st.text_input("Placement ID")
    name = st.text_input("Placement Name")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    base_cpm = st.number_input("Base CPM ($)", min_value=0.0, step=0.01)
    submitted = st.form_submit_button("Add Placement")
    if submitted:
        st.session_state.placements.append({
            "Placement ID": placement_id,
            "Name": name,
            "Start Date": start_date,
            "End Date": end_date,
            "Base CPM": base_cpm
        })

# Show placements
if st.session_state.placements:
    st.subheader("📋 Placements")
    placements_df = pd.DataFrame(st.session_state.placements)
    st.dataframe(placements_df)

# ---- BID FORM ----
st.header("💰 Submit Vendor Bid")
with st.form("bid_form"):
    vendor_name = st.text_input("Vendor Name")
    if st.session_state.placements:
        placement_options = [p["Placement ID"] for p in st.session_state.placements]
    else:
        placement_options = []
    selected_pid = st.selectbox("Placement ID", placement_options)
    bid_cpm = st.number_input("Max CPM Bid ($)", min_value=0.0, step=0.01)
    bid_start = st.date_input("Desired Start Date")
    bid_end = st.date_input("Desired End Date")
    note = st.text_input("Notes (optional)")
    bid_submitted = st.form_submit_button("Submit Bid")
    if bid_submitted:
        st.session_state.bids.append({
            "Vendor Name": vendor_name,
            "Placement ID": selected_pid,
            "Bid CPM": bid_cpm,
            "Start Date": bid_start,
            "End Date": bid_end,
            "Notes": note
        })

# Show bids
if st.session_state.bids:
    st.subheader("🗃 Vendor Bids")
    bids_df = pd.DataFrame(st.session_state.bids)
    st.dataframe(bids_df)

# ---- RUN AUCTION ----
st.header("🏁 Run Auction")

if st.button("Run Auction") and st.session_state.placements and st.session_state.bids:
    results = []
    delivery = []

    for placement in st.session_state.placements:
        pid = placement["Placement ID"]
        base_cpm = placement["Base CPM"]
        p_start = placement["Start Date"]
        p_end = placement["End Date"]

        # Filter bids for this placement
        relevant_bids = [b for b in st.session_state.bids if b["Placement ID"] == pid]

        if not relevant_bids:
            continue

        # Sort bids by CPM
        sorted_bids = sorted(relevant_bids, key=lambda x: x["Bid CPM"], reverse=True)
        winner = sorted_bids[0]
        winning_vendor = winner["Vendor Name"]

        if len(sorted_bids) > 1:
            winning_cpm = sorted_bids[1]["Bid CPM"] + 0.01
        else:
            winning_cpm = max(base_cpm, winner["Bid CPM"])

        results.append({
            "Placement ID": pid,
            "Winning Vendor": winning_vendor,
            "Winning CPM": round(winning_cpm, 2)
        })

        # Daily delivery entries
        delivery_range = pd.date_range(start=max(p_start, winner["Start Date"]),
                                       end=min(p_end, winner["End Date"]))
        for date in delivery_range:
            delivery.append({
                "Date": date,
                "Placement ID": pid,
                "Vendor": winning_vendor,
                "CPM": round(winning_cpm, 2),
                "Impressions": 10000,  # static for MVP
                "Spend": round((10000 / 1000) * winning_cpm, 2)
            })

    # Show results
    st.subheader("🏆 Auction Results")
    results_df = pd.DataFrame(results)
    st.dataframe(results_df)

    # Show daily delivery
    st.subheader("📅 Daily Delivery Plan")
    delivery_df = pd.DataFrame(delivery)
    st.dataframe(delivery_df)

    # Show summary
    st.subheader("📊 Vendor Summary")
    summary_df = delivery_df.groupby("Vendor").agg(
        Total_Impressions=("Impressions", "sum"),
        Total_Spend=("Spend", "sum"),
        Days_Booked=("Date", "nunique")
    ).reset_index()
    st.dataframe(summary_df)

    # Download buttons
    st.download_button("Download Daily Delivery CSV", data=delivery_df.to_csv(index=False), file_name="daily_delivery.csv")
    st.download_button("Download Summary CSV", data=summary_df.to_csv(index=False), file_name="summary.csv")
