import frappe
from a3_workshop_frontend.website_utils import require_login
from garagedesk.api.front_office import get_job_card_options

no_cache = 1

# `Jobcard Type` carries an optional `icon`, so a configured icon always wins. This map
# only supplies a glyph for the types that have none, and anything unmapped falls back to
# the same fa-wrench the wizard's Service Jobs step uses — a real job type is never hidden
# just because we have no icon for it.
_ICONS = {
	"service": "fa-screwdriver-wrench",
	"mechanical": "fa-gears",
	"electrical": "fa-car-battery",
	"computer": "fa-microchip",
	"body manufacturing": "fa-car-burst",
	"dending": "fa-hammer",
	"denting": "fa-hammer",
	"painting": "fa-spray-can",
	"inspection": "fa-magnifying-glass",
}
_DEFAULT_ICON = "fa-wrench"


def get_context(context):
	require_login(context)
	context.title = "Choose Job Type"
	context.page_icon = "fa-layer-group"
	context.subtitle = "Select the type of service or repair"
	context.breadcrumb = "Job Card"
	context.job_types = _job_types()
	return context


def _job_types():
	"""Active Jobcard Types, read through the same API call the wizard itself loads, so
	this first step and the wizard's Service Jobs step can never disagree. The caption is
	the type's own description, or a count of the Job Type Services configured under it."""
	options = get_job_card_options() or {}
	counts = {}
	for svc in options.get("job_type_services") or []:
		counts[svc.get("jobcard_type")] = counts.get(svc.get("jobcard_type"), 0) + 1

	types = []
	for row in options.get("jobcard_types") or []:
		label = row.get("type_name") or row.get("name")
		n = counts.get(row.get("name"), 0)
		types.append(
			{
				"name": row.get("name"),
				"label": label,
				"icon": row.get("icon") or _ICONS.get((label or "").strip().lower(), _DEFAULT_ICON),
				"sub": row.get("description")
				or ("%d service%s configured" % (n, "" if n == 1 else "s") if n else "No services configured yet"),
			}
		)
	return types
