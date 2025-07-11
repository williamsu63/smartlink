from flask import Flask, request, redirect, jsonify, render_template_string
from datetime import datetime
import csv
import os
from collections import defaultdict

app = Flask(__name__)

LOG_FILE = 'click_log.csv'

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'template_id', 'account_id', 'ip_address'])

@app.route('/')
def home():
    # landing page
    return "<h2>Smartlink Tracker is Live 🎯</h2><p>Use /redirect, /ctr, and /dashboard endpoints to test tracking.</p>"

# Logs clicks by redicrecting to destination URL
@app.route('/redirect')
def track_and_redirect():
    # Extract parameters from URL
    template_id = request.args.get('template_id')
    account_id = request.args.get('account_id')
    dest = request.args.get('dest')

    if not template_id or not dest or not account_id:
        return "Missing 'template_id', 'account_id', or 'dest' parameters", 400
    # Capture user's IP and timestamp
    user_ip = request.remote_addr
    timestamp = datetime.utcnow().isoformat()
    # Change CTR log
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, template_id, account_id, user_ip])
    # Redirect the user to the final destination URL
    return redirect(dest)

#CTR calculator
@app.route('/ctr')
def calculate_ctr():
    template_id = request.args.get('template_id')
    impressions = request.args.get('impressions', type=int)
    #validation
    if not template_id or impressions is None:
        return "Missing 'template_id' or 'impressions' parameters", 400
    # Count how many clicks match the template ID
    clicks = 0
    with open(LOG_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['template_id'] == template_id:
                clicks += 1
    # Return CTR
    ctr = clicks / impressions if impressions > 0 else 0
    return {
        "template_id": template_id,
        "clicks": clicks,
        "impressions": impressions,
        "ctr": round(ctr, 4)
    }

#Dashboard
@app.route('/dashboard')
def dashboard():
    template_id_filter = request.args.get('template_id')

    # If filtering by a specific template ID
    if template_id_filter:
        click_data = []
        with open(LOG_FILE) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['template_id'] == template_id_filter:
                    click_data.append((row['timestamp'], row['account_id']))

        # Return message if no data found
        if not click_data:
            return f"<h2>CTR Click Dashboard 📉</h2><p>Template ID: <strong>{template_id_filter}</strong></p><p>No click data available. Try visiting a tracked link first.</p>"

        # Table
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

    # Else show all clicks grouped by template ID
    else:
        click_data = defaultdict(list)
        with open(LOG_FILE) as f:
            reader = csv.DictReader(f)
            for row in reader:
                click_data[row['template_id']].append((row['timestamp'], row['account_id']))

        if not click_data:
            return f"<h2>CTR Click Dashboard 📉</h2><p>No click data available. Try visiting a tracked link first.</p>"
        rows = ''
        for template_id, data in sorted(click_data.items(), key=lambda x: len(x[1]), reverse=True):
            for timestamp, account_id in data:
                rows += f"<tr><td>{template_id}</td><td>{timestamp}</td><td>{account_id}</td></tr>"

        html = f"""
        <h2>CTR Click Dashboard 📊</h2>
        <table border="1" cellpadding="5">
            <thead><tr><th>Template ID</th><th>Timestamp</th><th>Account ID</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        """
        return html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
