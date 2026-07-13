import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Daily Planner"
	context.page_icon = "fa-calendar-day"
	context.subtitle = "Daily operations & quick actions"
	context.breadcrumb = "Daily Planner"
	return context
