# Import Modules
from flask import Flask, request, render_template
from datetime import time
import json
import matplotlib.pyplot as plt
import io
import base64
#from apscheduler.schedulers.background import BackgroundScheduler - HAven't been able to get this to work. 
# Import SQL Variables from SQL Query
from sqlquery import get_sql

# Get SQL Data on a scheduled job
timestamps, datavals, demand = get_sql()

#Define Flask App.
app = Flask(__name__)

# Define Home Route
@app.route("/")
def amchart():
    #Use SQL Variables
    vals = datavals
    # Inject SQL Variables into our amChart HTML template
    return render_template('amchart.html', values=vals)

# This function captures anything we post in the webpage
@app.route('/', methods=['POST'])
def my_form_post():
    vals = datavals
    text = request.form['text']
    processed_text = text.upper()
    return render_template('amchart.html',values=vals, value=processed_text)

# Create a chart in plotly.js
@app.route("/plotly")
def plotlychart():
    # Inject SQL Variables into our amChart HTML template
    return render_template('plotlychart.html', timesteps=timestamps, values=demand)

#Create a Matplotlib chart
@app.route('/matplotlib')
def build_plot():

    img = io.BytesIO()
    plt.plot(timestamps, demand, color='green', linewidth=0.75, label='SA Demand Forecast (MW)')  
    plt.savefig(img, format='png')
    plt.legend()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return '<img src="data:image/png;base64,{}">'.format(plot_url)

# Standard Flask step...
# If this is the script which is executed then run. If it is imported don't run. 
if __name__ == "__main__":
    app.run(debug=True)
