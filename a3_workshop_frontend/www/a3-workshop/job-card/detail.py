import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Job Card Detail"
	context.page_icon = "fa-clipboard-check"
	context.subtitle = ""
	context.breadcrumb = "Job Card"
	context.job_card_id = frappe.form_dict.get("id")
	return context
