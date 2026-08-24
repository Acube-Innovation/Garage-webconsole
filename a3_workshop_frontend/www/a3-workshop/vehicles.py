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

	# Batch-load the owning customers' phone + email for the Customer column, plus
	# the own-fleet flag the toolbar filters on. custom_is_own_fleet is a GarageDesk
	# fixture, so it is only asked for when the column is actually there.
	customer_ids = list({r.custom_customer for r in rows if r.custom_customer})
	has_fleet_flag = frappe.db.has_column("Customer", "custom_is_own_fleet")
	cust_info = {}
	if customer_ids:
		fields = ["name", "customer_name", "mobile_no", "email_id"]
		if has_fleet_flag:
			fields.append("custom_is_own_fleet")
		for c in frappe.get_all(
			"Customer",
			filters={"name": ["in", customer_ids]},
			fields=fields,
		):
			cust_info[c.name] = {
				"name": c.customer_name or c.name,
				"phone": c.mobile_no or "",
				"email": c.email_id or "",
				"is_own_fleet": bool(c.get("custom_is_own_fleet")) if has_fleet_flag else False,
			}

	# Which of these vehicles are on the floor right now — one grouped query, not
	# one per row. "In workshop" is any job card that is neither finished nor
	# scrapped, i.e. the same set the Job Cards page treats as live work.
	OPEN_JOB_STATUSES = ["Draft", "Open", "In Progress", "On Hold", "Ready"]
	in_workshop = set()
	if rows:
		in_workshop = {
			j.vehicle
			for j in frappe.get_all(
				"Workshop Job Card",
				filters={
					"vehicle": ["in", [r.name for r in rows]],
					"status": ["in", OPEN_JOB_STATUSES],
				},
				fields=["distinct vehicle as vehicle"],
			)
			if j.vehicle
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
				"customer_id": r.custom_customer or "",
				"customer_contact": phone or email or "—",
				"customer_contact_is_email": bool(not phone and email),
				"odometer": f"{odo:,.0f} km" if odo else "—",
				"fuel": r.fuel_type or "—",
				# --- toolbar filter facets
				"is_own_fleet": bool(info.get("is_own_fleet")),
				# Slugged so the chip's data-val is stable whatever the label reads
				# ("Natural Gas" -> "natural-gas").
				"fuel_slug": (r.fuel_type or "").strip().lower().replace(" ", "-") or "unknown",
				"in_workshop": r.name in in_workshop,
			}
		)

	context.vehicles = vehicles
	context.search = search
	return context
