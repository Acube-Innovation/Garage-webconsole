import frappe
from frappe.utils import now_datetime
from a3_workshop_frontend.website_utils import require_login, signature_of

no_cache = 1


def _driver_contact(driver, fallback_name):
	"""Name, mobile, licence number and signature for one side of a handover.

	The declaration and the signature block are the part of this print that gets
	signed and filed, so whoever took the vehicle has to be identifiable by more
	than a first name. `driver` is the Driver link on the handover; the stored
	`*_driver_name` rides along as the fallback for a record whose Driver row was
	renamed or removed.

	`signature` is what the print offers as the signature on file.
	"""
	info = {"name": fallback_name or "—", "phone": "", "license": "", "signature": ""}
	if not driver:
		return info
	row = frappe.db.get_value(
		"Driver", driver, ["full_name", "cell_number", "license_number"], as_dict=True
	)
	if not row:
		return info
	info["name"] = row.full_name or fallback_name or driver
	info["phone"] = row.cell_number or ""
	info["license"] = row.license_number or ""
	info["signature"] = signature_of("Driver", driver)
	return info


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
			["vehicle", "branch", "inspected_by", "customer_name", "customer",
			 "from_driver", "from_driver_name", "to_driver", "to_driver_name"],
			as_dict=True,
		)
		context.from_driver_info = _driver_contact(meta.from_driver, meta.from_driver_name)
		context.to_driver_info = _driver_contact(meta.to_driver, meta.to_driver_name)
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
		# One row in the signature chooser per rule at the foot of the document;
		# `id` matches the .sig-mark box the chosen image is dropped into. The
		# inspector signs as a user, not as a Driver, so that rule is upload-only.
		context.sig_slots = [
			{
				"id": "from_driver",
				"role": "From Driver",
				"name": context.h["from_driver"] if context.h["from_driver"] != "—" else "Returning Driver",
				"saved": context.from_driver_info["signature"],
			},
			{
				"id": "to_driver",
				"role": "To Driver",
				"name": context.h["to_driver"] if context.h["to_driver"] != "—" else "Receiving Driver",
				"saved": context.to_driver_info["signature"],
			},
			{"id": "inspector", "role": "Inspector", "name": context.h_meta["inspected_by"], "saved": ""},
		]
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
		context.sig_slots = [
			{"id": "driver", "role": "Driver", "name": context.driver_info.full_name or driver,
			 "saved": signature_of("Driver", driver)},
			{"id": "fleet_manager", "role": "Fleet Manager", "name": "", "saved": ""},
			{"id": "management", "role": "HR / Management", "name": "", "saved": ""},
		]
	elif customer and frappe.db.exists("Customer", customer):
		context.mode = "customer"
		context.d = fleet.get_customer_dashboard(customer)
		context.title = f"Fleet Summary — {context.d['customer_name']}"
	else:
		context.mode = "none"
		context.title = "Print"

	return context
