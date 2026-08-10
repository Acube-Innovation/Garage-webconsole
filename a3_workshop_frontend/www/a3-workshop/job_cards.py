import frappe
from frappe.utils import cint, flt, fmt_money

from a3_workshop_frontend.website_utils import require_login

no_cache = 1

# Job cards per page. The pager below is built from the real matching row count,
# so it disappears entirely when everything fits on one page.
PAGE_SIZE = 20

# Workshop Job Card status -> badge style used by the list. Keys are the real
# Select options on the doctype.
_STATUS_BADGE = {
	"Draft": "badge--soft",
	"Open": "badge--new",
	"In Progress": "badge--progress",
	"On Hold": "badge--pending",
	"Ready": "badge--navy",
	"Closed": "badge--success",
	"Completed": "badge--success",
	"Cancelled": "badge--soft",
}

# Statuses that take a card off the shop floor (same set daily_planner._CLOSED_JC
# and technician_board use).
_CLOSED_JC = ("Closed", "Completed", "Cancelled")

# Statuses the "Mark Done" toggle treats as finished work.
_DONE_JC = ("Completed", "Closed")


def get_context(context):
	require_login(context)
	context.title = "Job Cards"
	context.page_icon = "fa-clipboard-list"
	context.subtitle = "All job cards"
	context.breadcrumb = "Job Cards"

	# ?status= filters server-side; the options are the doctype's own Select
	# options, so the control can never offer a state the data cannot hold.
	context.statuses = _status_options()
	status = (frappe.form_dict.get("status") or "").strip()
	context.status = status if status in context.statuses else ""

	filters = {"status": context.status} if context.status else {}
	context.total = frappe.db.count("Workshop Job Card", filters)
	context.pages = max(1, -(-context.total // PAGE_SIZE))  # ceil
	context.page = max(1, min(cint(frappe.form_dict.get("page")) or 1, context.pages))
	context.page_links = _page_links(context.page, context.pages)

	start = (context.page - 1) * PAGE_SIZE
	context.rows = _job_card_rows(filters, start, PAGE_SIZE)
	context.range_from = start + 1 if context.rows else 0
	context.range_to = start + len(context.rows)

	# Team Workload is computed over EVERY job card, not just this page, so
	# paging or filtering the list never changes what the sidebar claims.
	context.workload = _advisor_workload()

	# The status toggle writes through core Frappe's whitelisted
	# frappe.client.set_value, which saves the doc and so enforces Workshop Job
	# Card write permission server-side. Hide the control from users who do not
	# hold that permission rather than render a button that cannot work.
	context.can_update = frappe.has_permission("Workshop Job Card", "write")
	return context


def _status_options():
	field = frappe.get_meta("Workshop Job Card").get_field("status")
	return [o.strip() for o in (field.options or "").split("\n") if o.strip()]


def _page_links(page, pages):
	"""Page numbers to render; None marks an elided gap."""
	if pages <= 7:
		return list(range(1, pages + 1))
	wanted = {1, pages, page}
	wanted.update(p for p in (page - 1, page + 1) if 1 <= p <= pages)
	out, prev = [], 0
	for p in sorted(wanted):
		if prev and p - prev > 1:
			out.append(None)
		out.append(p)
		prev = p
	return out


def _currency():
	"""Company default currency — never a hardcoded symbol."""
	company = frappe.defaults.get_user_default("Company") or frappe.db.get_default("company")
	return (
		frappe.get_cached_value("Company", company, "default_currency") if company else None
	) or frappe.db.get_default("currency")


def _job_card_rows(filters, start, limit):
	cards = frappe.get_all(
		"Workshop Job Card",
		filters=filters,
		fields=[
			"name",
			"customer",
			"mobile_no",
			"booking_date",
			"status",
			"service_advisor",
			"billing_total",
			"sales_order",
		],
		order_by="modified desc",
		limit_start=start,
		limit_page_length=limit,
	)
	if not cards:
		return []

	names = [c.name for c in cards]

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

	svc_map = _service_summary(names)
	advisor_names = _employee_names([c.service_advisor for c in cards])
	invoices = _invoices(names)
	currency = _currency()

	rows = []
	for c in cards:
		cust = cust_map.get(c.customer) or {}
		name = cust.get("customer_name") or c.customer or "Unknown Customer"
		# phone if available, else email
		contact = c.mobile_no or cust.get("mobile_no") or cust.get("email_id") or ""
		svc = svc_map.get(c.name) or {}
		status = c.status or "Draft"
		done = status in _DONE_JC
		si = invoices.get(c.name)
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
				"status": status,
				"sv": _STATUS_BADGE.get(status, "badge--soft"),
				# Money: the card's own Billing Total, formatted in the company
				# currency. Blank (not "0.00") while the card has not been billed.
				"amount": fmt_money(flt(c.billing_total), currency=currency)
				if flt(c.billing_total)
				else "",
				# Billing trail, only where the document really exists: a Sales
				# Invoice linked back through its `custom_job_card` field, else the
				# Sales Order the card already raised.
				"invoice": si.get("name") if si else "",
				"invoice_note": _invoice_note(si, currency),
				"sales_order": c.sales_order or "",
				"done": done,
				"next_status": "Open" if done else "Completed",
				"action": "Reopen" if done else "Mark Done",
			}
		)
	return rows


def _service_summary(card_names):
	"""{job card: {first job type, total estimated hours}} from its service rows."""
	out = {}
	if not card_names:
		return out
	for s in frappe.get_all(
		"Workshop Job Card Service",
		filters={"parent": ["in", card_names], "parenttype": "Workshop Job Card"},
		fields=["parent", "jobtype", "hours"],
		order_by="parent asc, idx asc",
		limit_page_length=0,
	):
		e = out.setdefault(s.parent, {"first": None, "hours": 0.0})
		if not e["first"] and s.jobtype:
			e["first"] = s.jobtype
		e["hours"] += flt(s.hours)
	return out


def _employee_names(employees):
	ids = list({e for e in employees if e})
	if not ids:
		return {}
	return {
		e.name: (e.employee_name or e.name)
		for e in frappe.get_all(
			"Employee",
			filters={"name": ["in", ids]},
			fields=["name", "employee_name"],
			limit_page_length=0,
		)
	}


def _invoices(card_names):
	"""{job card: newest live Sales Invoice} — the link is Sales Invoice.custom_job_card
	(a real Link field to Workshop Job Card); cancelled invoices are ignored."""
	out = {}
	if not card_names:
		return out
	for si in frappe.get_all(
		"Sales Invoice",
		filters={"custom_job_card": ["in", card_names], "docstatus": ["<", 2]},
		fields=["name", "custom_job_card", "status", "docstatus", "outstanding_amount"],
		order_by="creation desc",
		limit_page_length=0,
	):
		out.setdefault(si.custom_job_card, si)
	return out


def _invoice_note(si, currency):
	"""One honest line under the invoice number: what is still owed on it, or the
	invoice's own state when nothing is outstanding."""
	if not si:
		return ""
	if cint(si.docstatus) == 0:
		return "Draft invoice"
	if flt(si.outstanding_amount) > 0:
		return "Outstanding " + fmt_money(flt(si.outstanding_amount), currency=currency)
	return si.status or "Settled"


def _advisor_workload():
	"""Open vs. finished job cards per service advisor, across the whole table.

	There is no capacity / shift-length field on Employee, so this reports only
	what is recorded: card counts and the estimated hours on the cards still open.
	"""
	cards = frappe.get_all(
		"Workshop Job Card",
		filters={"service_advisor": ["is", "set"]},
		fields=["name", "status", "service_advisor"],
		limit_page_length=0,
	)
	if not cards:
		return []

	open_cards = [c for c in cards if (c.status or "Draft") not in _CLOSED_JC]
	hours = _service_summary([c.name for c in open_cards])
	names = _employee_names([c.service_advisor for c in cards])

	by_advisor = {}
	for c in cards:
		e = by_advisor.setdefault(
			c.service_advisor,
			{
				"employee": c.service_advisor,
				"name": names.get(c.service_advisor) or c.service_advisor,
				"total": 0,
				"open": 0,
				"hours": 0.0,
			},
		)
		e["total"] += 1
	for c in open_cards:
		e = by_advisor[c.service_advisor]
		e["open"] += 1
		e["hours"] += (hours.get(c.name) or {}).get("hours") or 0.0

	out = []
	for e in by_advisor.values():
		e["hours"] = round(e["hours"], 1)
		e["closed"] = e["total"] - e["open"]
		e["pct"] = round((e["closed"] / e["total"]) * 100) if e["total"] else 0
		out.append(e)
	out.sort(key=lambda e: (-e["open"], -e["total"], e["name"]))
	return out
