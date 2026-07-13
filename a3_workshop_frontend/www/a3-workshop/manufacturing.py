import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def get_context(context):
	require_login(context)
	context.title = "Manufacturing"
	context.page_icon = "fa-industry"
	context.subtitle = "Truck body production — work order to delivery"
	context.breadcrumb = "Manufacturing"
	return context
