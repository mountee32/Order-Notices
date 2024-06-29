## order_statistics.py

import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('my_logger')

def update_order_statistics(orders):
		logger.info(f"Updating order statistics for {len(orders)} orders")
		now = datetime.now()
		stats = {
				'24h': {'total_orders': 0, 'total_revenue': 0, 'new_customers': set()},
				'7d': {'total_orders': 0, 'total_revenue': 0, 'new_customers': set()},
				'30d': {'total_orders': 0, 'total_revenue': 0, 'new_customers': set()}
		}

		for order in orders:
				order_date = datetime.strptime(order['date_created'], "%Y-%m-%dT%H:%M:%S")
				customer_id = order['customer_id']
				total = float(order['total'])

				if now - order_date <= timedelta(hours=24):
						stats['24h']['total_orders'] += 1
						stats['24h']['total_revenue'] += total
						stats['24h']['new_customers'].add(customer_id)

				if now - order_date <= timedelta(days=7):
						stats['7d']['total_orders'] += 1
						stats['7d']['total_revenue'] += total
						stats['7d']['new_customers'].add(customer_id)

				if now - order_date <= timedelta(days=30):
						stats['30d']['total_orders'] += 1
						stats['30d']['total_revenue'] += total
						stats['30d']['new_customers'].add(customer_id)

		for period in stats:
				stats[period]['new_customers'] = len(stats[period]['new_customers'])
				stats[period]['avg_order_value'] = stats[period]['total_revenue'] / stats[period]['total_orders'] if stats[period]['total_orders'] > 0 else 0

		logger.info(f"Calculated statistics: {stats}")

		try:
				with open('order_statistics.json', 'w') as f:
						json.dump(stats, f)
				logger.info("Successfully wrote order statistics to file")
		except Exception as e:
				logger.error(f"Error writing order statistics to file: {str(e)}")

		logger.info("Finished updating order statistics")

def get_order_statistics():
		try:
				with open('order_statistics.json', 'r') as f:
						stats = json.load(f)
						logger.debug(f"Successfully read order statistics: {stats}")
						return stats
		except FileNotFoundError:
				logger.error("order_statistics.json file not found")
				return {}
		except json.JSONDecodeError:
				logger.error("Error decoding order_statistics.json")
				return {}
		except Exception as e:
				logger.error(f"Unexpected error reading order_statistics.json: {str(e)}")
				return {}
