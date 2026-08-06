import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Live Stock"
	context.page_icon = "fa-boxes-stacked"
	context.subtitle = "Stock monitoring board — warehouses, alerts, requisitions & payments"
	context.breadcrumb = "Live Stock"

	# One read-only call assembles the whole board (garagedesk.api.live_stock);
	# page actions reuse the existing garagedesk.api.workshop.create_material_request.
	from garagedesk.api.live_stock import get_stock_board

	context.board = get_stock_board()
	return context
