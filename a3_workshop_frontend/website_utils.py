import frappe


def require_login(context=None):
	"""Redirect Guests to the login page, preserving the originally requested path.

	Used by the Workshop website pages under ``www/a3-workshop`` so every page is gated
	behind login. Call from a page's ``get_context``.
	"""
	if frappe.session.user == "Guest":
		redirect_to = frappe.request.path if frappe.request else "/a3-workshop"
		frappe.local.flags.redirect_location = f"/login?redirect-to={redirect_to}"
		raise frappe.Redirect

	return context
