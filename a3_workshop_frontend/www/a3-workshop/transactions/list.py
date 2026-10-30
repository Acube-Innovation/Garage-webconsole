from urllib.parse import quote

import frappe
from frappe.utils import getdate

from a3_workshop_frontend.website_utils import require_transactions_access

no_cache = 1

# Reached as /a3-workshop/transactions/<slug> (hooks.website_route_rules); the
# route's <slug> lands in form_dict next to the query string filters.

_ICONS = {
	"material-request": "fa-clipboard-list",
	"purchase-order": "fa-file-signature",
	"purchase-receipt": "fa-truck-ramp-box",
	"purchase-invoice": "fa-file-invoice-dollar",
}

# The filters the form posts back, in the order the pager re-appends them.
_FILTER_KEYS = ("view", "status", "supplier", "q", "from_date", "to_date")


def get_context(context):
	require_transactions_access(context)
	from garagedesk.api.transactions import DOCTYPES, get_list

	slug = (frappe.form_dict.get("slug") or "").strip()
	if slug not in DOCTYPES:
		frappe.local.flags.redirect_location = "/a3-workshop/transactions"
		raise frappe.Redirect

	doctype = DOCTYPES[slug]
	context.slug = slug
	context.doctype = doctype
	context.doctypes = DOCTYPES
	context.title = doctype + "s"
	context.page_icon = _ICONS[slug]
	context.subtitle = "Purchasing · " + doctype
	context.breadcrumb = "Transactions"

	f = {k: (frappe.form_dict.get(k) or "").strip() for k in _FILTER_KEYS}
	for k in ("from_date", "to_date"):
		try:
			f[k] = str(getdate(f[k])) if f[k] else ""
		except Exception:
			f[k] = ""  # a hand-typed bad date is ignored, not a 500
	if f["view"] not in ("draft", "pending"):
		f["view"] = ""
	context.f = f

	# Paged server-side (garagedesk.api.transactions.PAGE_SIZE); the search box
	# matches the document id, the supplier and the linked Workshop Job Card.
	data = get_list(
		doctype,
		status=f["status"] or None,
		view=f["view"] or None,
		supplier=f["supplier"] or None,
		search=f["q"] or None,
		from_date=f["from_date"] or None,
		to_date=f["to_date"] or None,
		page=frappe.form_dict.get("page") or 1,
	)
	context.data = data
	context.rows = data["rows"]
	context.page = data["page"]
	context.pages = data["pages"]
	context.page_links = _page_links(data["page"], data["pages"])
	start = (data["page"] - 1) * data["page_size"]
	context.range_from = start + 1 if data["rows"] else 0
	context.range_to = start + len(data["rows"])
	context.filtered = any(f.values())
	# Query string of the active filters, for the pager links.
	context.qs = "&".join(f"{k}={quote(v)}" for k, v in f.items() if v)

	# Supplier filter: a datalist of real suppliers. Material Requests have none.
	context.has_supplier = doctype != "Material Request"
	context.suppliers = frappe.get_all(
		"Supplier", filters={"disabled": 0}, fields=["name", "supplier_name"],
		order_by="supplier_name asc", limit_page_length=500,
	) if context.has_supplier else []

	context.page_count = data["total"]
	context.page_count_label = "matching" if context.filtered else doctype + "s"
	return context


def _page_links(page, pages):
	"""Page numbers to render; None marks an elided gap (same as job_cards.py)."""
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
