# app.py

from flask import Flask, request, render_template_string, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///browser_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the BrowserData model
class BrowserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime)
    active_duration = db.Column(db.Integer)  # Duration in milliseconds

# Create the database table if it doesn't exist
if not os.path.exists('browser_data.db'):
    with app.app_context():
        db.create_all()

# Endpoint to receive browser data and display the report
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json()
        if data:
            new_entry = BrowserData(
                domain=data.get('domain'),
                timestamp=datetime.fromtimestamp(data.get('closeTime') / 1000),
                active_duration=data.get('activeDuration')
            )
            db.session.add(new_entry)
            db.session.commit()
        return '', 200

    else:
        # Calculate the date range for the past week
        today = datetime.now().date()
        week_ago = today - timedelta(days=6)  # Past 7 days including today

        # Query data for the past week
        start_datetime = datetime.combine(week_ago, datetime.min.time())
        end_datetime = datetime.combine(today, datetime.max.time())

        weekly_data = BrowserData.query.filter(
            BrowserData.timestamp >= start_datetime,
            BrowserData.timestamp <= end_datetime
        ).all()

        # Aggregate data by day and site
        daily_usage = {}
        site_usage = {}

        for entry in weekly_data:
            day = entry.timestamp.date()
            domain = entry.domain
            duration = entry.active_duration / 1000 / 60  # Convert to minutes

            # Aggregate daily usage
            if day not in daily_usage:
                daily_usage[day] = 0
            daily_usage[day] += duration

            # Aggregate site usage
            if domain not in site_usage:
                site_usage[domain] = 0
            site_usage[domain] += duration

        # Prepare data for chart
        chart_labels = []
        chart_data = []

        for i in range(7):
            day = week_ago + timedelta(days=i)
            chart_labels.append(day.strftime('%a %d %b'))
            chart_data.append(round(daily_usage.get(day, 0), 2))  # Minutes

        # Sort site usage
        sorted_sites = sorted(site_usage.items(), key=lambda x: x[1], reverse=True)
        sorted_sites_json = [{'domain': domain, 'active_duration': duration} for domain, duration in sorted_sites]

        # Inline HTML template using render_template_string
        template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Weekly Browser Activity Report</title>
            <!-- Include Chart.js -->
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { text-align: center; }
                .chart-container { width: 80%; margin: 0 auto; }
                table { width: 80%; margin: 20px auto; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Weekly Browser Activity Report</h1>
            <div class="chart-container">
                <canvas id="usageChart"></canvas>
            </div>
            <h2 style="text-align: center;">Top Sites This Week</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Domain</th>
                        <th>Total Time Spent (minutes)</th>
                    </tr>
                </thead>
                <tbody id="top-sites-table">
                    {% for site in sorted_sites %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ site.domain }}</td>
                        <td>{{ site.active_duration | round(2) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <script>
                var ctx = document.getElementById('usageChart').getContext('2d');
                var usageChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: {{ chart_labels | tojson }},
                        datasets: [{
                            label: 'Time Spent (minutes)',
                            data: {{ chart_data | tojson }},
                            backgroundColor: 'rgba(54, 162, 235, 0.5)'
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 10
                                }
                            }
                        }
                    }
                });

                // Function to update the chart and table dynamically
                function updateData() {
                    fetch('/browser_data')
                        .then(response => response.json())
                        .then(data => {
                            // Update chart labels and data
                            usageChart.data.labels = data.chart_labels;
                            usageChart.data.datasets[0].data = data.chart_data;
                            usageChart.update();

                            // Update the top sites table
                            const tableBody = document.getElementById('top-sites-table');
                            tableBody.innerHTML = '';  // Clear existing table rows

                            data.sorted_sites.forEach((site, index) => {
                                const row = document.createElement('tr');

                                const rankCell = document.createElement('td');
                                rankCell.textContent = index + 1;

                                const domainCell = document.createElement('td');
                                domainCell.textContent = site.domain;

                                const durationCell = document.createElement('td');
                                durationCell.textContent = site.active_duration.toFixed(2);

                                row.appendChild(rankCell);
                                row.appendChild(domainCell);
                                row.appendChild(durationCell);

                                tableBody.appendChild(row);
                            });
                        })
                        .catch(error => console.error('Error fetching data:', error));
                }

                // Fetch and update data every 30 seconds
                setInterval(updateData, 30000);  // 30000 milliseconds = 30 seconds

                // Optionally, fetch data immediately after page load
                window.onload = updateData;
            </script>
        </body>
        </html>
        '''

        return render_template_string(template,
                                      chart_labels=chart_labels,
                                      chart_data=chart_data,
                                      sorted_sites=sorted_sites_json)

# API endpoint for dynamic updates
@app.route('/browser_data')
def browser_data():
    # Calculate the date range for the past week
    today = datetime.now().date()
    week_ago = today - timedelta(days=6)  # Past 7 days including today

    # Query data for the past week
    start_datetime = datetime.combine(week_ago, datetime.min.time())
    end_datetime = datetime.combine(today, datetime.max.time())

    weekly_data = BrowserData.query.filter(
        BrowserData.timestamp >= start_datetime,
        BrowserData.timestamp <= end_datetime
    ).all()

    # Aggregate data by day and site
    daily_usage = {}
    site_usage = {}

    for entry in weekly_data:
        day = entry.timestamp.date()
        domain = entry.domain
        duration = entry.active_duration / 1000 / 60  # Convert to minutes

        # Aggregate daily usage
        if day not in daily_usage:
            daily_usage[day] = 0
        daily_usage[day] += duration

        # Aggregate site usage
        if domain not in site_usage:
            site_usage[domain] = 0
        site_usage[domain] += duration

    # Prepare data for chart
    chart_labels = []
    chart_data = []

    for i in range(7):
        day = week_ago + timedelta(days=i)
        chart_labels.append(day.strftime('%a %d %b'))
        chart_data.append(round(daily_usage.get(day, 0), 2))  # Minutes

    # Sort site usage
    sorted_sites = sorted(site_usage.items(), key=lambda x: x[1], reverse=True)
    sorted_sites_json = [{'domain': domain, 'active_duration': duration} for domain, duration in sorted_sites]

    return jsonify({
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'sorted_sites': sorted_sites_json
    })

if __name__ == '__main__':
    app.run(debug=True, port=8080)
 
