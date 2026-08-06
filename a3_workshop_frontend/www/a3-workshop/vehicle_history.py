import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Vehicle History"
	context.page_icon = "fa-clock-rotate-left"
	context.breadcrumb = "Vehicle History"

	# Two modes: no ?customer -> the customer picker; ?customer=... -> that
	# customer's dashboard. Data loads client-side from garagedesk.api.fleet so the
	# page works for front-desk roles that hold no Vehicle/Customer DocPerm.
	customer = (frappe.form_dict.get("customer") or "").strip()
	if customer and not frappe.db.exists("Customer", customer):
		customer = ""

	context.customer = customer
	if customer:
		context.subtitle = "Customer fleet dashboard"
		context.customer_label = (
			frappe.db.get_value("Customer", customer, "customer_name") or customer
		)
	else:
		context.subtitle = "Select a customer to view vehicle history"
		context.customer_label = ""
	context.search = (frappe.form_dict.get("q") or "").strip()

	# The Workshop Manager-only fleet toggle on the picker cards.
	roles = set(frappe.get_roles())
	context.can_toggle_fleet = bool(
		roles & {"Workshop Manager", "GarageDesk Admin", "System Manager"}
	)
	return context
