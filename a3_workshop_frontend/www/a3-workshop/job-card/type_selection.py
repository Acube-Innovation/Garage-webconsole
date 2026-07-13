import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Choose Job Type"
	context.page_icon = "fa-layer-group"
	context.subtitle = "Select the type of service or repair"
	context.breadcrumb = "Job Card"
	return context
