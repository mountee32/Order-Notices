import base64
import html
import json
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging.handlers
import requests
from dotenv import load_dotenv
load_dotenv()

log_file_path = "log.txt"
logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
file_handler = logging.handlers.RotatingFileHandler(log_file_path, backupCount=3)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = os.environ["SMTP_SENDER"]
smtp_password = os.environ["SMTP_PSW"]
CONSUMER_KEY = os.environ["KEY"]
CONSUMER_SECRET = os.environ["SECRET"]
recipient_emails = os.environ['SMTP_TO']
orders_url = os.environ['ORDERS_URL']

auth = base64.b64encode(f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode("utf-8")).decode("utf-8")

headers = {
		"Content-Type": "application/json",
		"Authorization": f"Basic {auth}"
}

processed_orders_file = "processed_orders.json"
pending_orders_file = "pending_orders.json"

try:
		with open(processed_orders_file, "r") as f:
				processed_orders = set(json.load(f))
				logger.info(f"Read {len(processed_orders)} existing orders previously processed")
except FileNotFoundError:
		processed_orders = set()
		logger.info("No existing processed orders found")

try:
		with open(pending_orders_file, "r") as f:
				pending_orders = set(json.load(f))
				logger.info(f"Read {len(pending_orders)} existing orders previously marked as pending")
except FileNotFoundError:
		pending_orders = set()
		logger.info("No existing pending orders found")

statuses = ["pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"]
status_counts = {}

for status in statuses:
		response = requests.get(f"{orders_url}?status={status}", headers=headers)
		status_counts[status] = response.headers["X-WP-Total"]
		logger.info(f"Number of orders in '{status}' status: {status_counts[status]}")

all_orders = []
page = 1

while True:
		response = requests.get(f"{orders_url}?per_page=100&page={page}", headers=headers)
		if response.json():
				orders = response.json()
				all_orders.extend(orders)
				logger.info(f"Read {len(orders)} orders from WooCommerce in 'processing' or 'pending' state (page {page})")
				page += 1
		else:
				break

new_orders = [
		order for order in all_orders
		if (order["status"] == "processing" and order["id"] not in processed_orders)
		or (order["status"] == "pending" and order["id"] not in pending_orders)
]
logger.info(f"{len(new_orders)} orders have not been previously processed or marked as pending and will be processed now")

for order in new_orders:
		logger.info(f"Processing order ID: {order['id']}")

		packing_slip = "Customer Details:\n"
		packing_slip += f"Name: {html.unescape(order['shipping']['first_name'])} {html.unescape(order['shipping']['last_name'])}\n"
		packing_slip += f"Shipping Address: {html.unescape(order['shipping']['address_1'])}, {html.unescape(order['shipping']['city'])}, {html.unescape(order['shipping']['state'])} {html.unescape(order['shipping']['postcode'])}, {html.unescape(order['shipping']['country'])}\n\n"
		packing_slip += "Order Details:\n"
		packing_slip += f"Order Number: {order['id']}\n"
		order_date = datetime.strptime(order["date_created"], "%Y-%m-%dT%H:%M:%S")
		packing_slip += f"Order Date: {order_date.strftime('%Y-%m-%d %I:%M %p')}\n"
		packing_slip += f"Payment Method: {html.unescape(order['payment_method_title'])}\n\n"
		packing_slip += "Items:\n"

		for idx, line_item in enumerate(order["line_items"], start=1):
				packing_slip += f"\n{idx}. {html.unescape(line_item['name'])} x {line_item['quantity']}\n"
				for meta in line_item["meta_data"]:
						if meta["display_key"] and meta["display_value"] and meta["display_key"] != "_wapf_meta":
								display_value = meta["display_value"]
								if "(+$" in display_value:
										display_value = display_value.split("(+$")[0].strip()
								packing_slip += f"   {html.unescape(meta['display_key'])}: {html.unescape(display_value)}\n"

		if order["customer_note"]:
				packing_slip += f"\nCustomer Note: {html.unescape(order['customer_note'])}\n"

		packing_slip += "\n--------------------"

		msg = MIMEMultipart()
		if order["status"] == "processing":
				msg["Subject"] = f"New Order - Order ID {order['id']}"
		else:
				msg["Subject"] = f"Pending Order - Order ID {order['id']}"
		msg["From"] = smtp_username
		msg['To'] = recipient_emails

		text = MIMEText(packing_slip)
		msg.attach(text)

		try:
				with smtplib.SMTP(smtp_server, smtp_port) as server:
						server.starttls()
						server.login(smtp_username, smtp_password)
						server.send_message(msg)
						logger.info(f"Email sent for order ID {order['id']}")
		except smtplib.SMTPException as e:
				logger.error(f"Error sending email for order ID {order['id']}: {e}")

		print(packing_slip)

		if order["status"] == "processing":
				processed_orders.add(order['id'])
		else:
				pending_orders.add(order['id'])

with open(processed_orders_file, 'w') as f:
		json.dump(list(processed_orders), f)
		logger.info(f"Saved {len(processed_orders)} processed orders to the JSON file")

with open(pending_orders_file, 'w') as f:
		json.dump(list(pending_orders), f)
		logger.info(f"Saved {len(pending_orders)} pending orders to the JSON file")