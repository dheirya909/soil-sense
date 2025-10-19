import streamlit as st
import requests
import pandas as pd
import time
import matplotlib.pyplot as plt
from io import StringIO

# =============================
# CONFIGURATION
# =============================
ESP_IP = "http://192.168.4.1/data"
MAX_POINTS = 50  # maximum number of points in live chart

# =============================
# STREAMLIT PAGE SETUP
# =============================
st.set_page_config(page_title="SOIL SENSE", layout="centered")
st.title("🌱 SOIL SENSE - Soil & Environment Monitor")

# =============================
# SPLASH SCREEN
# =============================
with st.spinner("🚀 Loading SOIL SENSE... Please wait!"):
    time.sleep(2)  # simulate loading time

# =============================
# DATA DISPLAY AREAS
# =============================
status_col, temp_col, hum_col, moist_col = st.columns(4)

status_text = status_col.empty()
temp_text = temp_col.empty()
hum_text = hum_col.empty()
moist_text = moist_col.empty()

# =============================
# LOG DATA STORAGE
# =============================
log_data = pd.DataFrame(columns=["Time", "Temperature", "Humidity", "Soil Moisture"])

# =============================
# LIVE CHART PLACEHOLDER
# =============================
chart_placeholder = st.empty()

# =============================
# MAIN LOOP
# =============================
moist_values = []
hum_values = []
timestamps = []

# Streamlit requires a loop to be controlled; we use while + st.empty() updating elements
stop_button = st.button("Stop Monitoring")
running = True

while running:
    if stop_button:
        running = False
        st.warning("🛑 Monitoring stopped by user.")
        break

    try:
        res = requests.get(ESP_IP, timeout=3)
        if res.status_code == 200:
            data = res.json()
            temp = data.get("temperature")
            hum = data.get("humidity")
            moist = data.get("moisture")

            # Update status and metrics
            status_text.markdown("🟢 Connected")
            temp_text.markdown(f"🌡 **Temperature:** {temp:.1f} °C" if temp is not None else "-- °C")
            hum_text.markdown(f"💧 **Humidity:** {hum:.1f} %" if hum is not None else "-- %")
            moist_text.markdown(f"🌱 **Soil Moisture:** {moist:.1f} %" if moist is not None else "-- %")

            # Update live chart data
            if temp is not None and hum is not None and moist is not None:
                current_time = pd.Timestamp.now().strftime("%H:%M:%S")
                timestamps.append(current_time)
                moist_values.append(float(moist))
                hum_values.append(float(hum))

                # Limit data points
                if len(moist_values) > MAX_POINTS:
                    moist_values.pop(0)
                    hum_values.pop(0)
                    timestamps.pop(0)

                # Add to logs
                log_data = pd.concat([log_data, pd.DataFrame({
                    "Time": [current_time],
                    "Temperature": [temp],
                    "Humidity": [hum],
                    "Soil Moisture": [moist]
                })], ignore_index=True)

            # Plotting
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(timestamps, moist_values, color="limegreen", marker="o", label="Soil Moisture")
            ax.plot(timestamps, hum_values, color="deepskyblue", marker="s", label="Humidity")
            ax.set_xlabel("Time")
            ax.set_ylabel("Percentage (%)")
            ax.set_title("Soil Moisture & Humidity Trend")
            ax.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            chart_placeholder.pyplot(fig)
        else:
            status_text.markdown("🔴 Disconnected")
    except Exception as e:
        status_text.markdown(f"🔴 Disconnected ({e})")

    time.sleep(2)

# =============================
# DOWNLOAD LOGS BUTTON
# =============================
st.markdown("---")
st.subheader("📥 Download Logs")
if not log_data.empty:
    csv_buffer = StringIO()
    log_data.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download CSV",
        data=csv_buffer.getvalue(),
        file_name="soil_logs.csv",
        mime="text/csv"
    )
else:
    st.info("No data collected yet to download.")
