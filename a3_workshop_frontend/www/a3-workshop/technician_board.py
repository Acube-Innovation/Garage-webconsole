import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Technician Board"
	context.page_icon = "fa-screwdriver-wrench"
	context.subtitle = "Your assigned tasks & progress"
	context.breadcrumb = "Technician Board"
	return context
