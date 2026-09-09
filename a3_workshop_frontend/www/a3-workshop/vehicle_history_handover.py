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

	# Whether this user can actually file the handover, checked BEFORE the form is
	# offered. Without it an inspector walks the whole vehicle -- every panel, the
	# tyres, the photographs -- and only learns at Confirm that save_handover would
	# refuse them, with the work unrecoverable. Same roles the API enforces, read
	# from the API so the two can never drift.
	from garagedesk.api.fleet import _FLEET_WRITE_ROLES, can_write_fleet

	context.can_save = can_write_fleet()
	context.fleet_write_roles = ", ".join(_FLEET_WRITE_ROLES)
	return context
