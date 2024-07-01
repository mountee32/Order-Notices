## main.py

from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import os
from functools import wraps
from dotenv import load_dotenv
import time
import logging
from replit import db

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

# Add database log handler
class DatabaseLogHandler(logging.Handler):
		def emit(self, record):
				log_entry = self.format(record)
				if "log_entries" not in db:
						db["log_entries"] = []
				db["log_entries"].append(log_entry)
				# Keep only the last 1000 log entries
				db["log_entries"] = db["log_entries"][-1000:]

db_handler = DatabaseLogHandler()
db_handler.setLevel(logging.INFO)
db_handler.setFormatter(formatter)
logger.addHandler(db_handler)

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
				orders = db.get("processed_orders", [])
				logger.debug(f"Loaded {len(orders)} processed orders from Replit DB")
				return orders
		except Exception as e:
				logger.error(f"Error loading processed orders from Replit DB: {str(e)}")
				return []

def get_log_content():
		return "\n".join(db.get("log_entries", []))

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

@app.route('/delete_order', methods=['POST'])
@token_required
def delete_order():
		order_id = request.form.get('order_id')
		if not order_id:
				return jsonify({'success': False, 'message': 'No order ID provided'}), 400

		try:
				order_id = int(order_id)
				processed_orders = db.get("processed_orders", [])
				if order_id in processed_orders:
						processed_orders.remove(order_id)
						db["processed_orders"] = processed_orders
						logger.info(f"Order {order_id} removed from processed orders for reprocessing")
						return jsonify({'success': True, 'message': f'Order {order_id} removed for reprocessing'})
				else:
						return jsonify({'success': False, 'message': f'Order {order_id} not found in processed orders'}), 404
		except ValueError:
				return jsonify({'success': False, 'message': 'Invalid order ID'}), 400
		except Exception as e:
				logger.error(f"Error removing order {order_id} for reprocessing: {str(e)}")
				return jsonify({'success': False, 'message': 'An error occurred while removing the order for reprocessing'}), 500

if __name__ == '__main__':
		logger.info("Starting the application")
		scheduler = BackgroundScheduler()
		scheduler.add_job(background_task, 'interval', minutes=5)
		scheduler.start()
		logger.info("Scheduler started")
		app.run(host='0.0.0.0', port=8080)
