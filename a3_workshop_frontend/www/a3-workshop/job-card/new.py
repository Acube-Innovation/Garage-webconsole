import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Create Job Card"
	context.page_icon = "fa-clipboard-list"
	context.subtitle = "Create Job Card & Assign Advisor"
	context.breadcrumb = "Job Card"
	return context
