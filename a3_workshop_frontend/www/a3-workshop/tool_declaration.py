import frappe
from frappe.utils import flt, formatdate, getdate, now_datetime, nowdate

from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	"""Printable tool responsibility declaration. One route, two documents:

	?technician=<Employee>  -> Custody Statement: every tool the technician holds
	                           right now, with one declaration covering all of them.
	?custody=<Tool Custody> -> Handover Slip: the tools moved by one submitted
	                           document, signed at the counter as they change hands.

	Both read the same custody state the Tools tab shows, so a printed declaration
	is always exactly what the board showed.
	"""
	require_login(context)

	fd = frappe.form_dict
	technician = (fd.get("technician") or "").strip()
	custody = (fd.get("custody") or "").strip()

	context.printed_on = now_datetime().strftime("%d %b %Y %H:%M")
	context.printed_by = (
		frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	)
	context.company = frappe.db.get_default("company") or (
		frappe.get_all("Company", pluck="name", order_by="creation", limit_page_length=1) or [""]
	)[0]
	context.mode = ""

	if custody and frappe.db.exists("Tool Custody", custody):
		_custody_slip(context, custody)
	elif technician and frappe.db.exists("Employee", technician):
		_custody_statement(context, technician)

	context.title = "Tool Responsibility Declaration"
	return context


def _emp(name):
	return (
		frappe.db.get_value(
			"Employee", name,
			["name", "employee_name", "designation", "department", "date_of_joining", "cell_number"],
			as_dict=True,
		)
		or frappe._dict()
	)


def _custody_statement(context, technician):
	"""Everything currently on one technician — the periodic sign-off."""
	from garagedesk.api.tool_custody import get_technician_tools

	context.mode = "statement"
	context.emp = _emp(technician)

	rows = get_technician_tools(technician)
	rates = _replacement_rates([r["item_code"] for r in rows])
	for r in rows:
		r["replacement_rate"] = flt(rates.get(r["item_code"]))
		r["since_fmt"] = (
			formatdate(r["custom_custody_since"], "dd MMM yyyy") if r["custom_custody_since"] else "—"
		)
		r["due_fmt"] = (
			formatdate(r["custom_expected_return_date"], "dd MMM yyyy")
			if r["custom_expected_return_date"]
			else "Permanent"
		)

	context.rows = rows
	context.total_value = sum(r["replacement_rate"] for r in rows)
	context.overdue_count = sum(1 for r in rows if r["overdue"])
	context.as_of = formatdate(nowdate(), "dd MMM yyyy")


def _custody_slip(context, custody):
	"""One submitted Tool Custody document — the counter slip."""
	doc = frappe.get_doc("Tool Custody", custody)
	if doc.docstatus == 2:
		context.mode = "cancelled"
		context.doc = doc
		return

	context.mode = "slip"
	context.doc = doc
	context.emp = _emp(doc.technician)
	context.to_emp = _emp(doc.to_technician) if doc.to_technician else None

	rates = _replacement_rates([r.item_code for r in doc.items])
	rows = []
	for r in doc.items:
		rows.append(
			{
				"serial_no": r.serial_no,
				"item_code": r.item_code,
				"item_name": r.item_name,
				"condition": r.condition or "Good",
				"remarks": r.remarks or "",
				"replacement_rate": flt(r.replacement_rate) or flt(rates.get(r.item_code)),
			}
		)
	context.rows = rows
	context.total_value = sum(r["replacement_rate"] for r in rows)
	context.txn_date = (
		formatdate(getdate(doc.transaction_date), "dd MMM yyyy") if doc.transaction_date else "—"
	)
	context.due_fmt = (
		formatdate(doc.expected_return_date, "dd MMM yyyy") if doc.expected_return_date else "Permanent"
	)
	context.is_draft = doc.docstatus == 0


def _replacement_rates(item_codes):
	codes = list({c for c in item_codes if c})
	if not codes:
		return {}
	return {
		i.name: i.custom_tool_replacement_value
		for i in frappe.get_all(
			"Item",
			filters={"name": ["in", codes]},
			fields=["name", "custom_tool_replacement_value"],
			limit_page_length=0,
		)
	}
