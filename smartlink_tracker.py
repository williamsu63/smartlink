from flask import Flask, request, redirect
from datetime import datetime
import csv
import os

app = Flask(__name__)

LOG_FILE = 'click_log.csv'

# Ensure log file has headers if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'template_id', 'ip_address'])

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

    # Redirect to destination
    return redirect(dest)

# Utility function for calculating CTR
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

if __name__ == '__main__':
    app.run(debug=True)
