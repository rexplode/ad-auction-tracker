
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime, timedelta
from fpdf import FPDF

st.set_page_config(page_title="Ad Auction Tool", layout="wide")
st.title("📢 Ad Auction Tracker (Enhanced UI)")

# Initialize session state
if "placements" not in st.session_state:
    st.session_state["placements"] = []
if "bids" not in st.session_state:
    st.session_state["bids"] = []
if "daily_delivery" not in st.session_state:
    st.session_state["daily_delivery"] = pd.DataFrame()

# Assign consistent vendor colors
vendor_colors = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    "#bcbd22", "#17becf"
]
vendor_color_map = {}

tab1, tab2 = st.tabs(["📋 Auction Builder", "📊 Vendor Reports"])

with tab1:
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

    if st.session_state.placements:
        st.subheader("📋 Placements")
        placements_df = pd.DataFrame(st.session_state.placements)
        st.dataframe(placements_df)

    st.header("💰 Submit Vendor Bid")
    with st.form("bid_form"):
        vendor_name = st.text_input("Vendor Name")
        placement_options = [p["Placement ID"] for p in st.session_state.placements]
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

    if st.session_state.bids:
        st.subheader("🗃 Vendor Bids")
        bids_df = pd.DataFrame(st.session_state.bids)
        st.dataframe(bids_df)

    st.header("🏁 Run Auction")

    if st.button("Run Auction") and st.session_state.placements and st.session_state.bids:
        results = []
        delivery = []

        for placement in st.session_state.placements:
            pid = placement["Placement ID"]
            base_cpm = placement["Base CPM"]
            p_start = placement["Start Date"]
            p_end = placement["End Date"]

            relevant_bids = [b for b in st.session_state.bids if b["Placement ID"] == pid]
            if not relevant_bids:
                continue

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

            delivery_range = pd.date_range(start=max(p_start, winner["Start Date"]),
                                           end=min(p_end, winner["End Date"]))
            for date in delivery_range:
                delivery.append({
                    "Date": date,
                    "Placement ID": pid,
                    "Vendor": winning_vendor,
                    "CPM": round(winning_cpm, 2),
                    "Impressions": 10000,
                    "Spend": round((10000 / 1000) * winning_cpm, 2)
                })

        delivery_df = pd.DataFrame(delivery)
        st.session_state["daily_delivery"] = delivery_df

        st.subheader("📅 Daily Delivery Plan")
        st.dataframe(delivery_df)

# ---------------------
# Vendor Reports Tab
# ---------------------
with tab2:
    st.header("🧾 Exportable Vendor Reports")
    dd_df = st.session_state["daily_delivery"]

    if not dd_df.empty:
        all_vendors = sorted(dd_df["Vendor"].unique())
        for i, v in enumerate(all_vendors):
            vendor_color_map[v] = vendor_colors[i % len(vendor_colors)]

        # Date selection UI at top right
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
        with col4:
            st.markdown("#### 📅 Select Date Range")

        with col1:
            if st.button("Last Week"):
                today = datetime.today()
                start_filter = today - timedelta(days=7)
                end_filter = today
            elif st.button("This Week"):
                today = datetime.today()
                start_filter = today - timedelta(days=today.weekday())
                end_filter = today
            elif st.button("Last Month"):
                today = datetime.today()
                start_filter = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
                end_filter = today.replace(day=1) - timedelta(days=1)
            else:
                start_filter = dd_df["Date"].min()
                end_filter = dd_df["Date"].max()

        start_date = col2.date_input("Start Date", value=start_filter)
        end_date = col3.date_input("End Date", value=end_filter)

        filtered_df = dd_df[(dd_df["Date"] >= pd.to_datetime(start_date)) & (dd_df["Date"] <= pd.to_datetime(end_date))]

        for vendor in all_vendors:
            with st.expander(f"📈 {vendor}", expanded=False):
                vendor_df = filtered_df[filtered_df["Vendor"] == vendor]
                if vendor_df.empty:
                    st.info("No data for this vendor in selected date range.")
                    continue

                chart_df = vendor_df.groupby(["Date", "Placement ID"])["Spend"].sum().unstack().fillna(0)
                fig, ax = plt.subplots()
                chart_df.plot(kind="line", ax=ax, marker="o", color=[vendor_color_map[vendor]] * len(chart_df.columns))
                ax.set_title(f"Spend Over Time by Placement - {vendor}")
                ax.set_ylabel("Spend ($)")
                ax.set_xlabel("Date")
                ax.grid(True)
                st.pyplot(fig)

                summary = vendor_df.agg(
                    Total_Impressions=("Impressions", "sum"),
                    Total_Spend=("Spend", "sum"),
                    Days_Booked=("Date", "nunique")
                )

                st.markdown(f"**Total Spend:** ${summary.Total_Spend:.2f}")
                st.markdown(f"**Total Impressions:** {int(summary.Total_Impressions)}")
                st.markdown(f"**Days Booked:** {summary.Days_Booked}")

                # Generate PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"Ad Auction Report for {vendor}", ln=True, align="C")
                pdf.ln(10)
                pdf.cell(200, 10, txt=f"Date Range: {start_date} to {end_date}", ln=True)
                pdf.ln(5)
                pdf.cell(200, 10, txt=f"Total Spend: ${summary.Total_Spend:.2f}", ln=True)
                pdf.cell(200, 10, txt=f"Total Impressions: {int(summary.Total_Impressions)}", ln=True)
                pdf.cell(200, 10, txt=f"Days Booked: {summary.Days_Booked}", ln=True)

                pdf_output = BytesIO()
                pdf.output(pdf_output)
                pdf_output.seek(0)

                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_output,
                    file_name=f"{vendor}_ad_report.pdf",
                    mime="application/pdf"
                )
    else:
        st.info("Run the auction first to generate delivery data.")
