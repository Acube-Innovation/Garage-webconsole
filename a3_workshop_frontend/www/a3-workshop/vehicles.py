import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def _customer_location(customer):
	"""Short location (city) from the customer's primary/linked Address."""
	addr_name = frappe.db.get_value("Customer", customer, "customer_primary_address")
	if not addr_name:
		link = frappe.get_all(
			"Dynamic Link",
			filters={"parenttype": "Address", "link_doctype": "Customer", "link_name": customer},
			fields=["parent"],
			limit=1,
		)
		addr_name = link[0].parent if link else None
	if not addr_name:
		return ""
	city = frappe.db.get_value("Address", addr_name, "city")
	return "" if (not city or city == "Not Specified") else city


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
			["make", "like", like],
			["model", "like", like],
			["custom_vin", "like", like],
		]

	rows = frappe.get_list(
		"Vehicle",
		fields=[
			"name",
			"make",
			"model",
			"custom_make",
			"custom_model",
			"custom_plate",
			"license_plate",
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

	# Batch-load the owning customers' phone + location for the Customer column.
	customer_ids = list({r.custom_customer for r in rows if r.custom_customer})
	cust_info = {}
	if customer_ids:
		for c in frappe.get_all(
			"Customer",
			filters={"name": ["in", customer_ids]},
			fields=["name", "customer_name", "mobile_no"],
		):
			cust_info[c.name] = {"name": c.customer_name, "phone": c.mobile_no or "", "location": ""}
		for cid in customer_ids:
			cust_info.setdefault(cid, {"name": cid, "phone": "", "location": ""})
			cust_info[cid]["location"] = _customer_location(cid)

	vehicles = []
	for r in rows:
		make = r.custom_make or r.make or ""
		title = f"{make} {r.model or ''}".strip() or r.name
		odo = r.last_odometer or r.custom_odometer or 0
		info = cust_info.get(r.custom_customer, {})
		vehicles.append(
			{
				"name": r.name,
				"title": title,
				"plate": r.custom_plate or r.license_plate or "—",
				"chassis": r.custom_vin or "—",
				"odometer": f"{odo:,.0f} km" if odo else "—",
				"fuel": r.fuel_type or "—",
				"customer": info.get("name") or r.custom_customer_name or "—",
				"customer_phone": info.get("phone") or "—",
				"customer_location": info.get("location") or "—",
				# Status is fixed to "Delivered" for now (no workshop-status field yet).
				"status": "Delivered",
				"status_variant": "badge--success",
			}
		)

	context.vehicles = vehicles
	context.search = search
	return context
