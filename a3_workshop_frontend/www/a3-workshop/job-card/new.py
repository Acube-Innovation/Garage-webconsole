import frappe
from a3_workshop_frontend.website_utils import require_login
from frappe.utils import flt

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Create Job Card"
	context.page_icon = "fa-clipboard-list"
	context.subtitle = "Create Job Card & Assign Advisor"
	context.breadcrumb = "Job Card"
	company = _company()
	# Currency for every amount the wizard formats client-side — resolved from the
	# company, never hardcoded in the template.
	context.currency = (
		frappe.get_cached_value("Company", company, "default_currency") if company else None
	) or ""
	tax = _estimate_tax(company)
	context.tax_label = tax["label"] if tax else ""
	context.tax_rate = tax["rate"] if tax else 0
	context.tax_rate_display = ("%g" % tax["rate"]) if tax else ""  # 5.0 -> "5", 7.5 -> "7.5"
	return context


def _company():
	return (
		frappe.defaults.get_user_default("Company")
		or frappe.db.get_default("company")
		or (frappe.get_all("Company", pluck="name", limit=1) or [None])[0]
	)


def _estimate_tax(company):
	"""The tax line for the Estimate tab, read from the company's default Sales Taxes and
	Charges Template. Returns None when no usable template exists, and the estimate then
	shows no tax row at all — a made-up percentage on a customer-facing quote is worse
	than no percentage.

	Only "On Net Total" rows can be used: the estimate applies one rate to the cart
	subtotal, so a template built on actual amounts or on previous-row totals cannot be
	reduced to a single percentage. Taxes on the real document are still whatever ERPNext
	computes on the Quotation this tab creates.
	"""
	if not company:
		return None

	# Only the template the company actually marks as default. There used to be a
	# fallback to the most recently modified one, which is not a default -- it is
	# whichever template someone last touched. On a company carrying the usual UAE
	# set (VAT 5%, VAT Zero, Exempted, Excise 50%, Excise 100%) that picked
	# "Excise 100%" and quietly doubled every estimate on screen.
	#
	# With no default set the estimate shows no tax row, which is the same answer
	# this gives when a company has no template at all, and is the honest one: a
	# rate nobody chose is worse on a customer-facing quote than no rate.
	name = frappe.db.get_value(
		"Sales Taxes and Charges Template", {"company": company, "is_default": 1, "disabled": 0}, "name"
	)
	if not name:
		return None

	rows = frappe.get_all(
		"Sales Taxes and Charges",
		filters={
			"parenttype": "Sales Taxes and Charges Template",
			"parent": name,
			"charge_type": "On Net Total",
		},
		fields=["rate", "description"],
		order_by="idx",
	)
	rate = sum(flt(r.rate) for r in rows)
	if not rate:
		return None
	return {"rate": rate, "label": (rows[0].description or "Tax") if len(rows) == 1 else "Tax"}
