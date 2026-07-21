import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Manufacturing"
	context.page_icon = "fa-industry"
	context.subtitle = "Manufacture items to stock — work order to delivery"
	context.breadcrumb = "Manufacturing"
	# The page is data-driven entirely through garagedesk.api.manufacturing.*
	# (see the <script> in manufacturing.html). Nothing is prefetched here so the
	# list, KPI cards and detail panel always reflect live Work Order data.
	return context
