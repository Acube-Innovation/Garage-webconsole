import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Telecalling"
	context.page_icon = "fa-phone-volume"
	context.subtitle = "Feedback & follow-ups"
	context.breadcrumb = "Telecalling"

	# Productivity tiles are rendered server-side from real Call Log / Workshop
	# Appointment counts (garagedesk.api.telecalling), so a JS failure shows the
	# real numbers rather than placeholders. The page JS only refreshes them.
	from garagedesk.api.telecalling import get_productivity, zero_productivity

	try:
		context.productivity = get_productivity()
	except Exception:
		context.productivity = zero_productivity()
	return context
