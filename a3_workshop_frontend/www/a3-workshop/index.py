import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Home"
	context.page_icon = "fa-gauge-high"
	context.subtitle = ""
	context.breadcrumb = ""
	return context
