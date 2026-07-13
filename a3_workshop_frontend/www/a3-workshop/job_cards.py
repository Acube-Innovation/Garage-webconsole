import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Job Cards"
	context.page_icon = "fa-clipboard-list"
	context.subtitle = "All job cards"
	context.breadcrumb = "Job Cards"
	return context
