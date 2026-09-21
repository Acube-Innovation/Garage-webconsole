import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Register Vehicle"
	context.page_icon = "fa-car-on"
	context.subtitle = "Vehicle entry & job creation"
	context.breadcrumb = "Register Vehicle"
	# The kinds of attachment a fleet can register — the same master the handover
	# form ticks (Desk -> Handover Attachment Item).
	context.attachment_types = frappe.get_all(
		"Handover Attachment Item", filters={"is_active": 1},
		pluck="name", order_by="sort_order asc, item_name asc",
	)
	return context
