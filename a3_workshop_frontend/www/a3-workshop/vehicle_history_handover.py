import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Vehicle Handover"
	context.page_icon = "fa-right-left"
	context.subtitle = "Driver handover & condition checklist"
	context.breadcrumb = "Vehicle History"

	vehicle = (frappe.form_dict.get("vehicle") or "").strip()
	if vehicle and not frappe.db.exists("Vehicle", vehicle):
		vehicle = ""
	context.vehicle = vehicle
	return context
