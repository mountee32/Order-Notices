## main.py

from flask import Flask, render_template, request, redirect, url_for, abort
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import os
from functools import wraps
from dotenv import load_dotenv
import time
import json
import logging

# Import from both files
from order_processing import process_orders
from order_statistics import update_order_statistics, get_order_statistics

load_dotenv()

app = Flask(__name__)

# Use a secret token for authentication
SECRET_TOKEN = os.getenv('SECRET_TOKEN')
print(f"SECRET_TOKEN: {SECRET_TOKEN}")
# Global variable to control the background task
keep_running = True

# Configure logging
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # Change to DEBUG for more detailed logs
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Also keep console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def background_task():
		global keep_running
		while keep_running:
				logger.info("Starting background task")
				all_orders = process_orders()
				update_order_statistics(all_orders)
				logger.info("Background task completed")
				time.sleep(300)  # Run every 5 minutes

def token_required(f):
		@wraps(f)
		def decorated_function(*args, **kwargs):
				token = request.args.get('token')
				logger.info(f"Received token: {token}")  # Debugging log
				if token and token == SECRET_TOKEN:
						return f(*args, **kwargs)
				else:
						logger.warning("Invalid token received")
						abort(401)
		return decorated_function

def get_processed_orders():
		try:
				with open('processed_orders.json', 'r') as f:
						orders = json.load(f)
						logger.debug(f"Loaded {len(orders)} processed orders")
						return orders
		except FileNotFoundError:
				logger.warning("processed_orders.json not found")
				return []
		except json.JSONDecodeError:
				logger.error("Error decoding processed_orders.json")
				return []

def get_log_content():
		try:
				with open('log.txt', 'r') as f:
						content = f.read()
						logger.debug("Log content loaded successfully")
						return content
		except FileNotFoundError:
				logger.warning("log.txt not found")
				return "No log file found."

@app.route('/')
@token_required
def home():
		logger.info("Home route accessed")
		processed_orders = get_processed_orders()
		log_content = get_log_content()
		order_statistics = get_order_statistics()
		logger.info(f"Rendering home page with order_statistics: {order_statistics}")
		return render_template('home.html', status=keep_running, processed_orders=processed_orders, log_content=log_content, order_statistics=order_statistics)

@app.route('/toggle', methods=['POST'])
@token_required
def toggle():
		global keep_running
		keep_running = not keep_running
		logger.info(f"Background task toggled. New state: {'running' if keep_running else 'stopped'}")
		if keep_running:
				thread = threading.Thread(target=background_task)
				thread.start()
		return redirect(url_for('home', token=SECRET_TOKEN))

if __name__ == '__main__':
		logger.info("Starting the application")
		scheduler = BackgroundScheduler()
		scheduler.add_job(background_task, 'interval', minutes=5)
		scheduler.start()
		logger.info("Scheduler started")
		app.run(host='0.0.0.0', port=8080)
