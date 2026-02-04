import streamlit as st
import pandas as pd
import re
import csv
import time
import requests
from pathlib import Path

# Define constants
TIME_OUT = 5
MAX_URLS = 100

# Compile URL regex
url_regex = re.compile(
    r'https?://[^\s"<>()]+',
    re.IGNORECASE
)

# Functions (same as your script, adapted for Streamlit)
def classify_status(status_code):
    if 200 <= status_code <= 299:
        return "OK"
    if 300 <= status_code <= 399:
        return "REDIRECT"
    if status_code in (401, 403):
        return "PAYWALLED"
    if status_code in (404, 410):
        return "DEAD"
    return "UNREACHABLE"

def extract_urls(text):
    return set(url_regex.findall(text))

def check_url(url):
    try:
        start = time.time()
        response = requests.head(url, timeout=TIME_OUT, allow_redirects=True)
        elapsed = int((time.time() - start) * 1000)
        return response.status_code, elapsed
    except requests.RequestException:
        try:
            start = time.time()
            response = requests.get(url, timeout=TIME_OUT, allow_redirects=True)
            elapsed = int((time.time() - start) * 1000)
            return response.status_code, elapsed
        except requests.RequestException:
            return None, None

# Streamlit App
st.title("Reference URL Checker")
st.write("Upload your references.txt file to check the status of URLs.")

uploaded_file = st.file_uploader("Upload references.txt", type=["txt"])

if uploaded_file:
    # Read the uploaded file
    text = uploaded_file.read().decode("utf-8")
    # Extract URLs
    urls = list(extract_urls(text))
    if len(urls) > MAX_URLS:
        urls = urls[:MAX_URLS]
        st.warning(f"Limiting to first {MAX_URLS} URLs for performance.")

    if st.button("Start URL Check"):
        progress_bar = st.progress(0)
        results = []

        for idx, url in enumerate(urls):
            status, response_time = check_url(url)
            if status is None:
                category = "UNREACHABLE"
                status_code = ""
                response_time_str = ""
            else:
                category = classify_status(status)
                status_code = status
                response_time_str = str(response_time)

            results.append({
                "url": url,
                "status_code": status_code,
                "category": category,
                "response_time_ms": response_time_str
            })

            # Update progress
            progress_bar.progress((idx + 1) / len(urls))
            # Optional: add a small delay for better UX
            # time.sleep(0.1)

        # Convert results to DataFrame
        df = pd.DataFrame(results)

        st.success("URL Check Completed!")
        st.dataframe(df)

        # Download button for CSV report
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV Report",
            data=csv,
            file_name=str(Path("output/reference_rot_report.csv")),
            mime="text/csv"
        )