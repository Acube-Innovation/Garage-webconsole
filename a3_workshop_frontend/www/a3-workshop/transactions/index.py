import frappe
from a3_workshop_frontend.website_utils import require_transactions_access

no_cache = 1


def get_context(context):
	# Supervisors / System Managers only; anyone else is sent back to /a3-workshop.
	require_transactions_access(context)
	context.title = "Transactions"
	context.page_icon = "fa-file-invoice-dollar"
	context.subtitle = "Material Request → Purchase Order → Purchase Receipt → Purchase Invoice"
	context.breadcrumb = "Transactions"

	# One read-only call: counts and the latest five per document type
	# (garagedesk.api.transactions.get_hub). Every link on the page goes to the
	# portal's own list / detail pages, never to /app.
	from garagedesk.api.transactions import get_hub

	context.cards = get_hub()
	return context
