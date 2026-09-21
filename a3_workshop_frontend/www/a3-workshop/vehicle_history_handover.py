import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.page_icon = "fa-right-left"
	context.breadcrumb = "Vehicle History"

	# ?handover= opens a handover that was already filed, read-only: the same
	# page, the same tables, rebuilt from what was recorded. The Handovers tab's
	# View button used to open a summary dialog, which showed a digest of the
	# inspection rather than the inspection -- the walk-round rows, their remarks,
	# who was held responsible and the photographs against each row were all
	# missing from it.
	handover = (frappe.form_dict.get("handover") or "").strip()
	vehicle = (frappe.form_dict.get("vehicle") or "").strip()

	if handover and frappe.db.exists("Driver Vehicle Handover", handover):
		# The vehicle comes off the handover rather than the query string: they
		# could disagree, and the record is the one that is right.
		vehicle = frappe.db.get_value("Driver Vehicle Handover", handover, "vehicle") or ""
	else:
		handover = ""

	if vehicle and not frappe.db.exists("Vehicle", vehicle):
		vehicle = ""

	context.vehicle = vehicle
	context.handover = handover
	context.readonly = 1 if handover else 0
	context.title = "Handover Record" if handover else "Vehicle Handover"
	context.subtitle = (
		handover if handover else "Driver handover & condition checklist"
	)

	# Whether this user can actually file the handover, checked BEFORE the form is
	# offered. Without it an inspector walks the whole vehicle -- every panel, the
	# tyres, the photographs -- and only learns at Confirm that save_handover would
	# refuse them, with the work unrecoverable. Same roles the API enforces, read
	# from the API so the two can never drift.
	#
	# Irrelevant to a record being read back: nothing on that page saves, so a
	# user who may not file one is not warned about it.
	from garagedesk.api.fleet import _FLEET_WRITE_ROLES, can_write_fleet

	context.can_save = True if handover else can_write_fleet()
	context.fleet_write_roles = ", ".join(_FLEET_WRITE_ROLES)
	return context
