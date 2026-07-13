import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Complaints"
	context.page_icon = "fa-triangle-exclamation"
	context.subtitle = "Track & resolve complaints"
	context.breadcrumb = "Complaints"
	return context
