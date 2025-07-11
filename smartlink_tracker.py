from flask import Flask, request, redirect, jsonify, render_template_string
from datetime import datetime
import csv
import os
from collections import defaultdict

app = Flask(__name__)

LOG_FILE = 'click_log.csv'

# Ensure log file has headers if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'template_id', 'account_id', 'ip_address'])

@app.route('/')
def home():
    return "<h2>Smartlink Tracker is Live 🎯</h2><p>Use /redirect, /ctr, and /dashboard endpoints to test tracking.</p>"

@app.route('/redirect')
def track_and_redirect():
    template_id = request.args.get('template_id')
    account_id = request.args.get('account_id')
    dest = request.args.get('dest')

    if not template_id or not dest or not account_id:
        return "Missing 'template_id', 'account_id', or 'dest' parameters", 400

    user_ip = request.remote_addr
    timestamp = datetime.utcnow().isoformat()

    # Log the click
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, template_id, account_id, user_ip])

    return redirect(dest)

@app.route('/ctr')
def calculate_ctr():
    template_id = request.args.get('template_id')
    impressions = request.args.get('impressions', type=int)

    if not template_id or impressions is None:
        return "Missing 'template_id' or 'impressions' parameters", 400

    clicks = 0
    with open(LOG_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['template_id'] == template_id:
                clicks += 1

    ctr = clicks / impressions if impressions > 0 else 0
    return {
        "template_id": template_id,
        "clicks": clicks,
        "impressions": impressions,
        "ctr": round(ctr, 4)
    }

@app.route('/dashboard')
def dashboard():
    template_id_filter = request.args.get('template_id')

    if template_id_filter:
        click_data = []
        with open(LOG_FILE) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['template_id'] == template_id_filter:
                    click_data.append((row['timestamp'], row['account_id']))

        if not click_data:
            return f"<h2>CTR Click Dashboard 📉</h2><p>Template ID: <strong>{template_id_filter}</strong></p><p>No click data available. Try visiting a tracked link first.</p>"

        rows = ''.join(f"<tr><td>{time}</td><td>{acct}</td></tr>" for time, acct in click_data)
        html = f"""
            <h2>CTR Click Dashboard 📊</h2>
            <p>Template ID: <strong>{template_id_filter}</strong></p>
            <p>Total Clicks: <strong>{len(click_data)}</strong></p>
            <table border="1" cellpadding="5">
                <thead><tr><th>Timestamp</th><th>Account ID</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        """
        return html
    else:
        click_counts = defaultdict(int)
        with open(LOG_FILE) as f:
            reader = csv.DictReader(f)
            for row in reader:
                click_counts[row['template_id']] += 1

        if not click_counts:
            return f"<h2>CTR Click Dashboard 📉</h2><p>No click data available. Try visiting a tracked link first.</p>"

        sorted_counts = sorted(click_counts.items(), key=lambda x: x[1], reverse=True)
        rows = ''.join(f"<tr><td>{tid}</td><td>{count}</td></tr>" for tid, count in sorted_counts)
        html = f"""
        <h2>CTR Click Dashboard 📊</h2>
        <table border="1" cellpadding="5">
            <thead><tr><th>Template ID</th><th>Total Clicks</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        """
        return html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
