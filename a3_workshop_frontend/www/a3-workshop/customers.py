import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Customers"
	context.page_icon = "fa-users"
	context.subtitle = "Customer profiles"
	context.breadcrumb = "Customers"

	# One read-only call builds the whole grid: real Customers plus their visit
	# count, billed total and contact details (garagedesk.api.front_office).
	from garagedesk.api.front_office import list_customer_cards

	# ?q= filters server-side, the same pattern the Vehicles page uses.
	context.search = (frappe.form_dict.get("q") or "").strip()
	context.customers = list_customer_cards(search=context.search or None, limit=120)
	return context
