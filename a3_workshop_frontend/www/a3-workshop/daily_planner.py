import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Daily Planner"
	context.page_icon = "fa-calendar-day"
	context.subtitle = "Daily operations & quick actions"
	context.breadcrumb = "Daily Planner"

	# Section 1 — Today's Tasks & To-Do (real ERPNext Tasks, grouped by priority).
	from garagedesk.api.daily_planner import (
		get_assignee_options,
		get_cash_summary,
		get_lead_bookings,
		get_today_task_groups,
	)

	context.task_groups = get_today_task_groups()
	context.assignees = get_assignee_options()
	# Section 3 — Today's Bookings (real Leads: input time, customer, vehicle model).
	context.booking_slots = get_lead_bookings()
	# Section 6 — Cash & Bills Summary (real accounting).
	context.cash = get_cash_summary()
	# Section 9 — Purchase Requirements: Critical Stock (job-card parts short/below reorder)
	# and Reorder Level Reached (items at/below reorder level).
	from garagedesk.api.workshop import get_purchase_requirements

	context.purchase_requirements = get_purchase_requirements()
	return context
