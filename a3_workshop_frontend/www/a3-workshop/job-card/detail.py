import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1

# This template is reached by two URL shapes:
#   /a3-workshop/job-card/<name>          the pretty route (hooks.website_route_rules)
#   /a3-workshop/job-card/detail?id=<name>  the query form other pages link with
# The "<id>" route rule matches the second shape too, and Werkzeug's route args are
# merged into form_dict *after* the query string — so on the query form form_dict["id"]
# is the literal page name "detail". _requested_id() therefore looks at the query string
# first and never treats the page name as a job card id.
_PAGE_NAME = "detail"


def get_context(context):
	require_login(context)
	context.page_icon = "fa-clipboard-check"
	context.breadcrumb = "Job Card"

	# One read-only call assembles the page from the saved Workshop Job Card and its
	# child tables (garagedesk.api.front_office.get_job_card_detail): service rows and
	# the Task each one spawned, complaints, the billing kit tables, readings, photos.
	# It returns {} for an unknown id, and the template renders its not-found state —
	# no id, customer, vehicle, status or amount is ever invented here.
	from garagedesk.api.front_office import get_job_card_detail

	card = None
	requested = ""
	for candidate in _candidate_ids():
		requested = requested or candidate
		card = get_job_card_detail(candidate) or None
		if card:
			break

	# ?handover= — the card a handover is about to raise, shown before it exists.
	# The Handovers tab's "Create Job Card" lands here: same layout as a real card,
	# filled in from what the Damages popup planned, editable in place, and created
	# by the button at the top. A handover that already has a card shows that card
	# instead, so the page can never offer to raise a second one.
	handover = "" if card else (frappe.form_dict.get("handover") or "").strip()
	if handover:
		from garagedesk.api.handover_comparison import get_job_card_preview

		existing = frappe.get_all(
			"Workshop Job Card",
			filters={"handover": handover, "status": ["!=", "Cancelled"]},
			pluck="name", order_by="creation asc", limit_page_length=1,
		)
		if not existing:
			existing = [
				n for n in [frappe.db.get_value(
					"Driver Vehicle Handover", handover, "rectification_job_card")] if n
			]
		if existing:
			card = get_job_card_detail(existing[0]) or None
			requested = requested or existing[0]
			handover = ""
		else:
			card = get_job_card_preview(handover) or None
			if not card:
				handover = ""

	context.job_card_id = requested
	context.card = card
	context.handover = handover
	context.draft = 1 if (card and card.get("draft")) else 0

	if context.draft:
		context.title = "New Job Card"
		context.subtitle = " · ".join(
			[x for x in (card["customer_name"], card["vehicle_label"]) if x]
		)
	elif card:
		context.title = "Job Card " + card["name"]
		context.subtitle = " · ".join(
			[x for x in (card["customer_name"], card["vehicle_label"]) if x]
		)
	else:
		context.title = "Job Card"
		context.subtitle = "Job card not found"
	return context


def _candidate_ids():
	"""Ids the URL could be asking for, query string first, page name excluded."""
	args = frappe.request.args if getattr(frappe, "request", None) else {}
	ids = []
	for value in (args.get("id") if args else None, frappe.form_dict.get("id")):
		value = (value or "").strip()
		if value and value != _PAGE_NAME and value not in ids:
			ids.append(value)
	return ids
