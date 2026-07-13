import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Register Vehicle"
	context.page_icon = "fa-car-on"
	context.subtitle = "Vehicle entry & job creation"
	context.breadcrumb = "Register Vehicle"
	return context
