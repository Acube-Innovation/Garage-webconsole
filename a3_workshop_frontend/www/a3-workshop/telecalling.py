import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Telecalling"
	context.page_icon = "fa-phone-volume"
	context.subtitle = "Feedback & follow-ups"
	context.breadcrumb = "Telecalling"
	return context
