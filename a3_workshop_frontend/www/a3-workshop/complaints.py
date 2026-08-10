import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Complaints"
	context.page_icon = "fa-triangle-exclamation"
	context.subtitle = "Complaints recorded on job cards"
	context.breadcrumb = "Complaints"

	# One read-only call assembles the page (garagedesk.api.complaints) from the
	# Workshop Job Card Complaint child rows — the same query the printed
	# Complaints Register uses (workshop-print?complaints=register).
	from garagedesk.api.complaints import get_complaint_board

	context.board = get_complaint_board()
	return context
