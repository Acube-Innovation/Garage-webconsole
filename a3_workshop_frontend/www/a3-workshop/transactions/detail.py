import frappe
from a3_workshop_frontend.website_utils import require_transactions_access

no_cache = 1

# One template for two URL shapes (hooks.website_route_rules):
#   /a3-workshop/transactions/<slug>/<docname>   an existing document
#   /a3-workshop/transactions/<slug>/new         the create form
# The create form takes ?from=<source name> to be prefilled by ERPNext's mapper
# (Purchase Order from a Material Request, Receipt from an Order, Invoice from
# an Order or a Receipt), and for a Material Request ?type=Material%20Issue,
# ?job_card= and ?task=. Both shapes render the same editor; a new document is
# only written when the supervisor presses Save.

_ICONS = {
	"material-request": "fa-clipboard-list",
	"purchase-order": "fa-file-signature",
	"purchase-receipt": "fa-truck-ramp-box",
	"purchase-invoice": "fa-file-invoice-dollar",
}


def get_context(context):
	require_transactions_access(context)
	from garagedesk.api.transactions import DOCTYPES, get_doc, get_new

	slug = (frappe.form_dict.get("slug") or "").strip()
	if slug not in DOCTYPES:
		frappe.local.flags.redirect_location = "/a3-workshop/transactions"
		raise frappe.Redirect

	doctype = DOCTYPES[slug]
	docname = (frappe.form_dict.get("docname") or "").strip()
	args = frappe.request.args if getattr(frappe, "request", None) else {}
	source = ((args.get("from") if args else None) or "").strip()

	context.slug = slug
	context.doctype = doctype
	context.page_icon = _ICONS[slug]
	context.breadcrumb = "Transactions"
	context.list_url = "/a3-workshop/transactions/" + slug
	context.error = ""
	context.doc = None

	try:
		if docname:
			context.doc = get_doc(doctype, docname)
		else:
			context.doc = get_new(
				doctype,
				source_name=source or None,
				job_card=(args.get("job_card") if args else None),
				task=(args.get("task") if args else None),
				material_request_type=(args.get("type") if args else None),
			)
	except frappe.PermissionError:
		raise
	except frappe.DoesNotExistError:
		context.error = f"{doctype} {docname} was not found."
	except frappe.ValidationError as e:
		# e.g. ?from= names a draft, or everything on it was already carried forward.
		context.error = frappe.utils.strip_html(str(e)) or "This document could not be prepared."
	finally:
		# A caught frappe.throw must not resurface as a dialog on the next request.
		frappe.local.message_log = []

	d = context.doc
	if d and d["is_new"]:
		context.title = "New " + doctype
		context.subtitle = ("From " + d["source"]["doctype"] + " " + d["source"]["name"]) if d.get("source") else "Draft — not saved yet"
	elif d:
		context.title = doctype + " " + d["name"]
		context.subtitle = " · ".join(x for x in (d["supplier_name"] or d["material_request_type"], d["status"]) if x)
	else:
		context.title = doctype
		context.subtitle = "Not available"
	return context
