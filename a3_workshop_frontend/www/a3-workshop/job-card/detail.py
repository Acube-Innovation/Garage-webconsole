import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1

_STATUS_BADGE = {
	"Open": "badge--new",
	"In Progress": "badge--progress",
	"Completed": "badge--success",
}


def get_context(context):
	require_login(context)
	context.page_icon = "fa-clipboard-check"
	context.subtitle = ""
	context.breadcrumb = "Job Card"

	jc_id = frappe.form_dict.get("id")
	context.job_card_id = jc_id
	context.card = None

	if jc_id and frappe.db.exists("Workshop Job Card", jc_id):
		doc = frappe.get_doc("Workshop Job Card", jc_id)
		cust = (
			frappe.db.get_value("Customer", doc.customer, ["customer_name"], as_dict=True)
			if doc.customer
			else {}
		) or {}
		veh = (
			frappe.db.get_value(
				"Vehicle", doc.vehicle, ["make", "model", "custom_plate", "license_plate"], as_dict=True
			)
			if doc.vehicle
			else {}
		) or {}
		vlabel = " ".join([x for x in (veh.get("make"), veh.get("model")) if x])
		plate = veh.get("custom_plate") or veh.get("license_plate")
		if plate:
			vlabel = (vlabel + " · " + plate).strip(" ·")

		context.card = {
			"name": doc.name,
			"customer": cust.get("customer_name") or doc.customer or "—",
			"vehicle": vlabel or "—",
			"status": doc.status or "Open",
			"status_badge": _STATUS_BADGE.get(doc.status or "Open", "badge--soft"),
			"readings": {
				"odometer": doc.reading_odometer,
				"next_km": doc.next_service_km,
				"fuel": doc.fuel_level,
				"oil": doc.oil_level,
				"coolant": doc.coolant_level,
				"battery": doc.battery_voltage,
				"tyre": doc.tyre_condition,
				"spare": doc.spare_tyre,
			},
			"body_condition": doc.body_condition or "",
			"photos": [
				{"image": p.image, "caption": p.caption or ""} for p in (doc.vehicle_photos or [])
			],
		}
		context.title = "Job Card " + doc.name
	else:
		context.title = "Job Card Detail"
	return context
