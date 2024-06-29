from flask import Flask, render_template, request, redirect, url_for, abort
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import os
from functools import wraps
from dotenv import load_dotenv
import time
import json

# Import your existing script
from order_processing import process_orders

load_dotenv()

app = Flask(__name__)

# Use a secret token for authentication
SECRET_TOKEN = os.getenv('SECRET_TOKEN')
print(f"SECRET_TOKEN: {SECRET_TOKEN}")
# Global variable to control the background task
keep_running = True

def background_task():
		global keep_running
		while keep_running:
				process_orders()
				time.sleep(300)  # Run every 5 minutes

def token_required(f):
		@wraps(f)
		def decorated_function(*args, **kwargs):
				token = request.args.get('token')
				print(f"Received token: {token}")  # Debugging print
				if token and token == SECRET_TOKEN:
						return f(*args, **kwargs)
				else:
						abort(401)
		return decorated_function

def get_processed_orders():
		try:
				with open('processed_orders.json', 'r') as f:
						return json.load(f)
		except FileNotFoundError:
				return []

def get_log_content():
		try:
				with open('log.txt', 'r') as f:
						return f.read()
		except FileNotFoundError:
				return "No log file found."

@app.route('/')
@token_required
def home():
		processed_orders = get_processed_orders()
		log_content = get_log_content()
		return render_template('home.html', status=keep_running, processed_orders=processed_orders, log_content=log_content)

@app.route('/toggle', methods=['POST'])
@token_required
def toggle():
		global keep_running
		keep_running = not keep_running
		if keep_running:
				thread = threading.Thread(target=background_task)
				thread.start()
		return redirect(url_for('home', token=SECRET_TOKEN))

if __name__ == '__main__':
		scheduler = BackgroundScheduler()
		scheduler.add_job(background_task, 'interval', minutes=5)
		scheduler.start()
		app.run(host='0.0.0.0', port=8080)