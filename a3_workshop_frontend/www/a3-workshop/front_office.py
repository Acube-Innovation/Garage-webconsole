import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Front Office"
	context.page_icon = "fa-bell-concierge"
	context.subtitle = "Quick customer & vehicle entry"
	context.breadcrumb = "Front Office"
	return context
