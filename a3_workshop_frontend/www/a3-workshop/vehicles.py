import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Vehicles"
	context.page_icon = "fa-car"
	context.subtitle = "Vehicle master & lookup"
	context.breadcrumb = "Vehicles"

	search = (frappe.form_dict.get("q") or "").strip()
	or_filters = None
	if search:
		like = f"%{search}%"
		or_filters = [
			["custom_plate", "like", like],
			["license_plate", "like", like],
			["custom_model", "like", like],
			["model", "like", like],
			["chassis_no", "like", like],
			["custom_vin", "like", like],
		]

	rows = frappe.get_list(
		"Vehicle",
		fields=[
			"name",
			"model",
			"custom_model",
			"custom_plate",
			"license_plate",
			"chassis_no",
			"custom_vin",
			"last_odometer",
			"custom_odometer",
			"fuel_type",
			"custom_customer",
			"custom_customer_name",
		],
		or_filters=or_filters,
		order_by="modified desc",
		limit_page_length=200,
	)

	# Batch-load the owning customers' phone + email for the Customer column.
	customer_ids = list({r.custom_customer for r in rows if r.custom_customer})
	cust_info = {}
	if customer_ids:
		for c in frappe.get_all(
			"Customer",
			filters={"name": ["in", customer_ids]},
			fields=["name", "customer_name", "mobile_no", "email_id"],
		):
			cust_info[c.name] = {
				"name": c.customer_name or c.name,
				"phone": c.mobile_no or "",
				"email": c.email_id or "",
			}

	vehicles = []
	for r in rows:
		model = r.custom_model or r.model or r.name
		odo = r.custom_odometer or r.last_odometer or 0
		info = cust_info.get(r.custom_customer, {})
		# Column 2 shows the phone if we have one, otherwise fall back to the email.
		phone = info.get("phone") or ""
		email = info.get("email") or ""
		vehicles.append(
			{
				"name": r.name,
				"model": model,
				"plate": r.custom_plate or r.license_plate or "—",
				"chassis": r.chassis_no or r.custom_vin or "—",
				"customer": info.get("name") or r.custom_customer_name or "—",
				"customer_contact": phone or email or "—",
				"customer_contact_is_email": bool(not phone and email),
				"odometer": f"{odo:,.0f} km" if odo else "—",
				"fuel": r.fuel_type or "—",
			}
		)

	context.vehicles = vehicles
	context.search = search
	return context
