import frappe
from frappe.sessions import get_csrf_token
from frappe.utils import cint, flt, formatdate

from a3_workshop_frontend.website_utils import require_login

no_cache = 1

# Job Card statuses that take a card off the shop floor (same set the technician
# activity board in garagedesk.api.front_office uses).
_CLOSED_JC = ("Closed", "Completed", "Cancelled")

# Workshop Job Card status -> badge style (same map as the Job Cards list).
_JC_BADGE = {
	"Draft": "badge--soft",
	"Open": "badge--new",
	"In Progress": "badge--progress",
	"On Hold": "badge--pending",
	"Ready": "badge--success",
}

# ERPNext Task status -> badge style. Every Workshop Job Card Service row links a
# real Task, and that Task's `progress` (Percent) is what backs the % bar — there
# is no percentage field on the job card or on the service row itself.
_TASK_BADGE = {
	"Open": "badge--new",
	"Working": "badge--progress",
	"Pending Review": "badge--pending",
	"Overdue": "badge--danger",
	"Completed": "badge--success",
	"Cancelled": "badge--soft",
}


def get_context(context):
	require_login(context)

	# Ship a CSRF token that is guaranteed to be valid.
	#
	# `frappe.session.csrf_token` (the usual template idiom) reads whatever is
	# already on the session and renders the literal "None" when nothing has
	# generated one yet — which is the normal state right after login. The POST
	# still succeeds at that point, because Frappe skips CSRF validation when the
	# session holds no token at all. But as soon as anything else on that session
	# generates one (opening /app in another tab, for instance), the token baked
	# into this already-rendered page no longer matches and every write from it
	# fails with "Invalid Request".
	#
	# get_csrf_token() generates and persists a token when the session lacks one,
	# so the value rendered here always matches what validation will compare against.
	# get_csrf_token() persists through frappe.local.session_obj, which only exists
	# inside a real HTTP request. Fall back to whatever the session already carries
	# rather than letting a token lookup 500 the whole board.
	try:
		context.csrf_token = get_csrf_token()
	except Exception:
		session = getattr(frappe.local, "session", None)
		context.csrf_token = (getattr(session, "data", None) or {}).get("csrf_token") or ""

	context.title = "Technician Board"
	context.page_icon = "fa-screwdriver-wrench"
	context.breadcrumb = "Technician Board"

	# Scope. Employee.user_id is the link from a portal login to a technician, so
	# an Employee sees only their own assignments. A manager / Administrator with
	# no Employee record falls back to the whole floor.
	me = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user, "status": "Active"},
		["name", "employee_name"],
		as_dict=True,
	)
	context.me = me
	context.subtitle = (
		"Your assigned tasks & progress" if me else "All technicians' assigned tasks & progress"
	)

	context.groups = _assigned_work(me.name if me else None)
	context.totals = _totals(context.groups)
	# Only the floor-wide view names who is free; a technician's own board has no
	# use for it.
	context.idle = [] if me else _idle_technicians(context.groups)

	# The "Update Progress" control writes Task.progress through core Frappe's
	# whitelisted frappe.client.set_value, which saves the doc normally and so
	# enforces Task write permission server-side. Hide the control from users who
	# do not hold that permission rather than render a button that cannot work.
	context.can_update = frappe.has_permission("Task", "write")

	_tool_context(context, me)
	return context


# --------------------------------------------------------------------- tools


def _tool_context(context, me):
	"""Tools tab: who is holding which physical tool, and what is overdue.

	Everything here degrades to an empty board rather than breaking the page —
	the Tools tab is an addition to a board that already works, so a missing
	doctype (app not migrated) or a user without the custody roles must not take
	the Assignments tab down with it.
	"""
	context.tools = {"groups": [], "totals": {}}
	context.tool_kits = []
	context.tool_technicians = []
	context.can_manage_tools = False
	context.tools_error = ""

	if not frappe.db.exists("DocType", "Tool Custody"):
		context.tools_error = "Tool custody is not installed on this site yet."
		return

	try:
		from garagedesk.api.tool_custody import get_tool_board

		context.tools = get_tool_board(me.name if me else None)
	except frappe.PermissionError:
		context.tools_error = "You do not have access to the tool register."
		return
	except Exception:
		frappe.log_error(title="technician-board: tool tab")
		context.tools_error = "The tool register could not be read."
		return

	# Issue/return are real submitted documents, so mirror the server-side
	# permission rather than rendering buttons that will be rejected.
	context.can_manage_tools = frappe.has_permission("Tool Custody", "submit")

	if context.can_manage_tools:
		context.tool_kits = frappe.get_all(
			"Tool Kit Template",
			filters={"is_active": 1},
			fields=["name", "grade", "replacement_value"],
			order_by="name asc",
			limit_page_length=0,
		)
		context.tool_technicians = frappe.get_all(
			"Employee",
			filters={"status": "Active"},
			fields=["name", "employee_name", "designation"],
			order_by="employee_name asc",
			limit_page_length=0,
		)


def _assigned_work(employee):
	"""Open Workshop Job Card Service rows that carry a technician, grouped by
	technician. One card per service row = one real assignment."""
	filters = {"technician": employee} if employee else {"technician": ["is", "set"]}
	rows = frappe.get_all(
		"Workshop Job Card Service",
		filters=filters,
		fields=[
			"name",
			"parent",
			"idx",
			"service",
			"description",
			"jobtype",
			"technician",
			"hours",
			"task",
		],
		order_by="parent desc, idx asc",
		limit_page_length=0,
	)
	if not rows:
		return []

	cards = _job_cards([r.parent for r in rows])
	tasks = _tasks([r.task for r in rows if r.task])
	techs = _employee_names([r.technician for r in rows])
	labels = _service_labels([r.service for r in rows if r.service])

	by_tech = {}
	for r in rows:
		jc = cards.get(r.parent)
		if not jc or (jc.get("status") or "") in _CLOSED_JC:
			continue
		task = tasks.get(r.task) or {}
		qc_text, qc_variant = _qc_state(jc)
		hours = round(flt(r.hours), 1)
		group = by_tech.setdefault(
			r.technician,
			{
				"technician": r.technician,
				"technician_name": techs.get(r.technician) or r.technician,
				"rows": [],
				"hours": 0.0,
			},
		)
		group["rows"].append(
			{
				"job_card": r.parent,
				"customer": jc.get("customer_name") or "",
				"vehicle": jc.get("vehicle_label") or "",
				"label": (
					labels.get(r.service) or r.description or r.jobtype or r.service or "Service"
				),
				"hours": hours,
				# Progress + task status come from the linked ERPNext Task.
				"task": r.task or "",
				"tracked": bool(r.task),
				"task_status": task.get("status") or "",
				"task_badge": _TASK_BADGE.get(task.get("status") or "", "badge--soft"),
				"progress": max(0, min(100, cint(task.get("progress")))),
				# QC comes from the job card's own QC fields — nothing invented.
				"qc": qc_text,
				"qc_variant": qc_variant,
				"dvi": (jc.get("dvi_gate_status") or "Pending")
				if cint(jc.get("dvi_gate_required"))
				else "",
				"jc_status": jc.get("status") or "",
				"jc_badge": _JC_BADGE.get(jc.get("status") or "", "badge--soft"),
				"due": formatdate(jc.get("promised_delivery"), "dd MMM yyyy")
				if jc.get("promised_delivery")
				else "",
			}
		)
		group["hours"] += hours

	groups = []
	for group in by_tech.values():
		group["hours"] = round(group["hours"], 1)
		group["count"] = len(group["rows"])
		group["done"] = sum(1 for t in group["rows"] if t["tracked"] and t["progress"] >= 100)
		groups.append(group)
	groups.sort(key=lambda g: (-g["count"], -g["hours"], g["technician_name"]))
	return groups


def _qc_state(jc):
	"""QC badge straight off Workshop Job Card: `qc_passed` (Check) and, when the
	card requires it, `dvi_gate_status` (Pending/Passed/Failed)."""
	if cint(jc.get("qc_passed")):
		return "QC Passed", "badge--success"
	if cint(jc.get("dvi_gate_required")) and jc.get("dvi_gate_status") == "Failed":
		return "QC Failed", "badge--danger"
	return "QC Pending", "badge--pending"


def _job_cards(names):
	names = list({n for n in names if n})
	out = {}
	if not names:
		return out
	cards = frappe.get_all(
		"Workshop Job Card",
		filters={"name": ["in", names]},
		fields=[
			"name",
			"customer",
			"vehicle",
			"status",
			"qc_passed",
			"dvi_gate_required",
			"dvi_gate_status",
			"promised_delivery",
		],
		limit_page_length=0,
	)
	customers = _customer_names([c.customer for c in cards])
	vehicles = _vehicle_labels([c.vehicle for c in cards])
	for c in cards:
		c.customer_name = customers.get(c.customer) or c.customer or ""
		c.vehicle_label = vehicles.get(c.vehicle) or c.vehicle or ""
		out[c.name] = c
	return out


def _tasks(names):
	names = list({n for n in names if n})
	if not names:
		return {}
	return {
		t.name: t
		for t in frappe.get_all(
			"Task",
			filters={"name": ["in", names]},
			fields=["name", "subject", "status", "progress"],
			limit_page_length=0,
		)
	}


def _vehicle_labels(vehicles):
	ids = list({v for v in vehicles if v})
	out = {}
	if not ids:
		return out
	for v in frappe.get_all(
		"Vehicle",
		filters={"name": ["in", ids]},
		fields=["name", "make", "model", "custom_plate", "license_plate"],
		limit_page_length=0,
	):
		label = " ".join(x for x in (v.make, v.model) if x)
		plate = v.custom_plate or v.license_plate
		if plate:
			label = (label + " · " + plate).strip(" ·")
		out[v.name] = label or v.name
	return out


def _customer_names(customers):
	ids = list({c for c in customers if c})
	if not ids:
		return {}
	return {
		c.name: (c.customer_name or c.name)
		for c in frappe.get_all(
			"Customer",
			filters={"name": ["in", ids]},
			fields=["name", "customer_name"],
			limit_page_length=0,
		)
	}


def _employee_names(employees):
	ids = list({e for e in employees if e})
	if not ids:
		return {}
	return {
		e.name: (e.employee_name or e.name)
		for e in frappe.get_all(
			"Employee",
			filters={"name": ["in", ids]},
			fields=["name", "employee_name"],
			limit_page_length=0,
		)
	}


def _service_labels(services):
	ids = list({s for s in services if s})
	if not ids:
		return {}
	return {
		s.name: (s.service_name or s.name)
		for s in frappe.get_all(
			"Job Type Service",
			filters={"name": ["in", ids]},
			fields=["name", "service_name"],
			limit_page_length=0,
		)
	}


def _totals(groups):
	rows = [t for g in groups for t in g["rows"]]
	tracked = [t for t in rows if t["tracked"]]
	return {
		"tasks": len(rows),
		"job_cards": len({t["job_card"] for t in rows}),
		"hours": round(sum(t["hours"] for t in rows), 1),
		"technicians": len(groups),
		"tracked": len(tracked),
		"done": sum(1 for t in tracked if t["progress"] >= 100),
		"avg": round(sum(t["progress"] for t in tracked) / len(tracked)) if tracked else 0,
	}


def _idle_technicians(groups):
	"""Active Employees with nothing open on them — read off the same board the
	Daily Planner uses (garagedesk.api.front_office.get_technician_board)."""
	from garagedesk.api.front_office import get_technician_board

	busy = {g["technician"] for g in groups}
	return [t for t in get_technician_board() if t["name"] not in busy and not t["jobs"]]
