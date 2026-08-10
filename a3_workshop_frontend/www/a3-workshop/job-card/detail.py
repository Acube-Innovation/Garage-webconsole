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

	context.job_card_id = requested
	context.card = card

	if card:
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
