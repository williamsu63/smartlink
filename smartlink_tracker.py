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
        writer.writerow(['timestamp', 'template_id', 'ip_address'])

@app.route('/')
def home():
    return "<h2>Smartlink Tracker is Live 🎯</h2><p>Use /redirect, /ctr, and /dashboard endpoints to test tracking.</p>"

@app.route('/redirect')
def track_and_redirect():
    template_id = request.args.get('template_id')
    dest = request.args.get('dest')

    if not template_id or not dest:
        return "Missing 'template_id' or 'dest' parameters", 400

    user_ip = request.remote_addr
    timestamp = datetime.utcnow().isoformat()

    # Log the click
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, template_id, user_ip])

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
    daily_counts = defaultdict(int)

    with open(LOG_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if template_id_filter and row['template_id'] != template_id_filter:
                continue
            date = row['timestamp'][:10]  # Extract YYYY-MM-DD
            daily_counts[date] += 1

    dates = sorted(daily_counts.keys())
    counts = [daily_counts[date] for date in dates]

    html = '''
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h2>CTR Click Dashboard 📈</h2>
        <p>Template ID: <strong>{{ template_id }}</strong></p>
        <canvas id="clickChart" width="600" height="300"></canvas>
        <script>
            const ctx = document.getElementById('clickChart').getContext('2d');
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: {{ dates }},
                    datasets: [{
                        label: 'Clicks per Day',
                        data: {{ counts }},
                        borderColor: 'blue',
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, dates=dates, counts=counts, template_id=template_id_filter or "All")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
