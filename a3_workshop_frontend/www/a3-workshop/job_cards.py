import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1

# Workshop Job Card status -> badge style used by the list.
_STATUS_BADGE = {
	"Open": "badge--new",
	"In Progress": "badge--progress",
	"Completed": "badge--success",
}


def get_context(context):
	require_login(context)
	context.title = "Job Cards"
	context.page_icon = "fa-clipboard-list"
	context.subtitle = "All job cards"
	context.breadcrumb = "Job Cards"
	context.rows = _job_card_rows()
	return context


def _job_card_rows():
	cards = frappe.get_all(
		"Workshop Job Card",
		fields=["name", "customer", "mobile_no", "booking_date", "status", "service_advisor"],
		order_by="modified desc",
		limit_page_length=100,
	)
	if not cards:
		return []

	# Batch-load customers (name/phone/email/photo) and service lines (job type + hours).
	customer_ids = list({c.customer for c in cards if c.customer})
	cust_map = {}
	if customer_ids:
		for c in frappe.get_all(
			"Customer",
			filters={"name": ["in", customer_ids]},
			fields=["name", "customer_name", "mobile_no", "email_id", "image"],
		):
			cust_map[c.name] = c

	services = frappe.get_all(
		"Workshop Job Card Service",
		filters={"parent": ["in", [c.name for c in cards]]},
		fields=["parent", "jobtype", "hours"],
	)
	svc_map = {}
	for s in services:
		e = svc_map.setdefault(s.parent, {"first": None, "hours": 0.0})
		if not e["first"] and s.jobtype:
			e["first"] = s.jobtype
		e["hours"] += s.hours or 0

	advisor_names = {}
	for adv in {c.service_advisor for c in cards if c.service_advisor}:
		advisor_names[adv] = frappe.db.get_value("Employee", adv, "employee_name") or adv

	rows = []
	for c in cards:
		cust = cust_map.get(c.customer) or {}
		name = cust.get("customer_name") or c.customer or "Unknown Customer"
		# phone if available, else email
		contact = c.mobile_no or cust.get("mobile_no") or cust.get("email_id") or ""
		svc = svc_map.get(c.name) or {}
		rows.append(
			{
				"no": c.name,
				"customer": name,
				"initial": (name.strip()[0].upper() if name.strip() else "?"),
				"image": cust.get("image") or "",
				"contact": contact,
				"svc": svc.get("first") or "—",
				"date": frappe.utils.formatdate(c.booking_date, "dd MMM yyyy") if c.booking_date else "—",
				"advisor": advisor_names.get(c.service_advisor, ""),
				"est": round(svc.get("hours") or 0, 1),
				"status": c.status or "Open",
				"sv": _STATUS_BADGE.get(c.status or "Open", "badge--soft"),
			}
		)
	return rows
