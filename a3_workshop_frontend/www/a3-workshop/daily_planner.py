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
		get_bills_and_collections,
		get_cash_summary,
		get_followup_queue,
		get_job_card_pipeline,
		get_lead_bookings,
		get_pending_advances,
		get_task_form_options,
		get_technician_activity,
		get_today_task_groups,
	)

	context.task_groups = get_today_task_groups()
	context.assignees = get_assignee_options()
	# Link/select choices for the New Task form (only records that exist).
	context.task_form = get_task_form_options()
	# Section 2 — Job Cards In Progress (live cards bucketed into the five stages).
	context.pipeline = get_job_card_pipeline()
	# Section 3 — Today's Enquiries (Opportunities logged today: time, customer, vehicle).
	context.booking_slots = get_lead_bookings()
	# Section 4 — Customer Follow-Up Queue (approvals, ready vehicles, service dues, complaints).
	context.followups = get_followup_queue()
	# Section 5 — Technician Activity Board (same board as the Create Job Card page).
	context.techs = get_technician_activity()
	# Section 6 — Cash & Bills Summary (real accounting).
	context.cash = get_cash_summary()
	# Section 7 — Pending Advances (unallocated Payment Entries by party type).
	context.advances = get_pending_advances()
	# Section 8 — Pending Bills & Collections (aged receivables / payables).
	context.bills = get_bills_and_collections()
	# Section 9 — Purchase Requirements: Critical Stock (job-card parts short/below reorder)
	# and Reorder Level Reached (items at/below reorder level).
	from garagedesk.api.workshop import get_purchase_requirements

	context.purchase_requirements = get_purchase_requirements()
	return context
