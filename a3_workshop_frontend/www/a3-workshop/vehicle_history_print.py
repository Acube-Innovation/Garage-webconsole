import frappe
from frappe.utils import now_datetime
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	"""Print view for the Vehicle History module. One route, four documents:

	?vehicle=<plate>    -> Vehicle History Report (fleet AND outside customers)
	?customer=<name>    -> Customer Fleet Summary (stats, vehicles, KPI leaderboard)
	?handover=<name>    -> Handover Inspection Report (checklist, damages, diff, signatures)
	?driver=<name>      -> Driver Performance Report (scorecard + monthly trend)

	Data comes from the same garagedesk.api.fleet functions the on-screen pages
	use, so a print is always exactly what the screen showed.
	"""
	require_login(context)
	from garagedesk.api import fleet

	fd = frappe.form_dict
	handover = (fd.get("handover") or "").strip()
	vehicle = (fd.get("vehicle") or "").strip()
	driver = (fd.get("driver") or "").strip()
	customer = (fd.get("customer") or "").strip()

	context.printed_on = now_datetime().strftime("%d %b %Y %H:%M")
	context.printed_by = (
		frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	)
	# Passed through the context rather than read from the parent template's
	# {% set %}: Jinja does not expose a parent's module-level variables inside a
	# block the child overrides, so the handover declaration would render blank.
	context.company = frappe.db.get_default("company") or (
		frappe.get_all("Company", pluck="name", order_by="creation", limit_page_length=1) or [""]
	)[0]

	if handover and frappe.db.exists("Driver Vehicle Handover", handover):
		context.mode = "handover"
		context.h = fleet.get_handover(handover)
		meta = frappe.db.get_value(
			"Driver Vehicle Handover", handover,
			["vehicle", "branch", "inspected_by", "customer_name", "customer"],
			as_dict=True,
		)
		v = frappe.db.get_value(
			"Vehicle", meta.vehicle,
			["custom_model", "model", "custom_plate", "license_plate", "chassis_no", "custom_vin"],
			as_dict=True,
		) or frappe._dict()
		context.h_meta = {
			"model": v.custom_model or v.model or meta.vehicle,
			"plate": v.custom_plate or v.license_plate or meta.vehicle,
			"chassis": v.chassis_no or v.custom_vin or "—",
			"branch": meta.branch or "—",
			"inspected_by": (
				frappe.db.get_value("User", meta.inspected_by, "full_name") or meta.inspected_by or "—"
			),
			"customer": meta.customer_name
			or (frappe.db.get_value("Customer", meta.customer, "customer_name") if meta.customer else "")
			or "—",
		}
		context.title = f"Handover {handover}"
	elif vehicle and frappe.db.exists("Vehicle", vehicle):
		context.mode = "vehicle"
		context.d = fleet.get_vehicle_history(vehicle)
		context.title = f"Vehicle History — {vehicle}"
	elif driver and frappe.db.exists("Driver", driver):
		context.mode = "driver"
		context.s = fleet.get_driver_scorecard(driver)
		context.driver_info = frappe.db.get_value(
			"Driver", driver,
			["full_name", "cell_number", "license_number", "expiry_date", "status"],
			as_dict=True,
		)
		context.title = f"Driver Performance — {context.driver_info.full_name or driver}"
	elif customer and frappe.db.exists("Customer", customer):
		context.mode = "customer"
		context.d = fleet.get_customer_dashboard(customer)
		context.title = f"Fleet Summary — {context.d['customer_name']}"
	else:
		context.mode = "none"
		context.title = "Print"

	return context
