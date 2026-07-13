app_name = "a3_workshop_frontend"
app_title = "A3 Workshop Frontend"
app_publisher = "Acube Innovations Private Limited"
app_description = "Workshop Frontend App"
app_email = "admin@acube.co"
app_license = "mit"

# Website
# ------------------

# Map the dynamic job-card detail route to its template page. The catch-all
# <id> rule would also swallow /new and /type-selection, so those static
# sub-pages are mapped to themselves first. Werkzeug routing always prefers a
# static rule over a dynamic one, regardless of order.
website_route_rules = [
	{"from_route": "/a3-workshop/job-card/new", "to_route": "a3-workshop/job-card/new"},
	{"from_route": "/a3-workshop/job-card/type-selection", "to_route": "a3-workshop/job-card/type-selection"},
	{"from_route": "/a3-workshop/job-card/<id>", "to_route": "a3-workshop/job-card/detail"},
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "a3_workshop_frontend",
# 		"logo": "/assets/a3_workshop_frontend/logo.png",
# 		"title": "A3 Workshop Frontend",
# 		"route": "/a3_workshop_frontend",
# 		"has_permission": "a3_workshop_frontend.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/a3_workshop_frontend/css/a3_workshop_frontend.css"
# app_include_js = "/assets/a3_workshop_frontend/js/a3_workshop_frontend.js"

# include js, css files in header of web template
# web_include_css = "/assets/a3_workshop_frontend/css/a3_workshop_frontend.css"
# web_include_js = "/assets/a3_workshop_frontend/js/a3_workshop_frontend.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "a3_workshop_frontend/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "a3_workshop_frontend/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "a3_workshop_frontend.utils.jinja_methods",
# 	"filters": "a3_workshop_frontend.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "a3_workshop_frontend.install.before_install"
# after_install = "a3_workshop_frontend.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "a3_workshop_frontend.uninstall.before_uninstall"
# after_uninstall = "a3_workshop_frontend.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "a3_workshop_frontend.utils.before_app_install"
# after_app_install = "a3_workshop_frontend.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "a3_workshop_frontend.utils.before_app_uninstall"
# after_app_uninstall = "a3_workshop_frontend.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "a3_workshop_frontend.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"a3_workshop_frontend.tasks.all"
# 	],
# 	"daily": [
# 		"a3_workshop_frontend.tasks.daily"
# 	],
# 	"hourly": [
# 		"a3_workshop_frontend.tasks.hourly"
# 	],
# 	"weekly": [
# 		"a3_workshop_frontend.tasks.weekly"
# 	],
# 	"monthly": [
# 		"a3_workshop_frontend.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "a3_workshop_frontend.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "a3_workshop_frontend.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "a3_workshop_frontend.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["a3_workshop_frontend.utils.before_request"]
# after_request = ["a3_workshop_frontend.utils.after_request"]

# Job Events
# ----------
# before_job = ["a3_workshop_frontend.utils.before_job"]
# after_job = ["a3_workshop_frontend.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"a3_workshop_frontend.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

