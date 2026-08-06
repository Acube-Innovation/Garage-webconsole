"""Print views for the wider workshop portal. One route, eight documents:

	?jobcard=<name>      -> Job Card sheet (readings, body condition, services, photos)
	?invoice=<name>      -> Sales Invoice
	?receipt=<name>      -> Payment Receipt (Payment Entry)
	?statement=<cust>    -> Customer Account Statement (job cards, invoices, payments)
	?dayplan=[date]      -> Daily Planner day sheet (open tasks by priority)
	?workorder=<name>    -> Work Order traveler (stages, materials, operations)
	?complaints=register -> Complaints register (real Workshop Job Card Complaint rows)
	?calls=[date]        -> Telecalling call list for a day

Everything here is READ-ONLY: direct queries + reuse of existing read APIs. No
existing module is modified; the on-screen pages only gained print buttons.
"""

import frappe
from frappe import _
from frappe.utils import (
	cint,
	flt,
	formatdate,
	get_datetime,
	getdate,
	now_datetime,
	nowdate,
)
from a3_workshop_frontend.website_utils import require_login

no_cache = 1


def _fmt_date(v):
	return formatdate(v, "dd MMM yyyy") if v else "—"


def _fmt_dt(v):
	return get_datetime(v).strftime("%d %b %Y %H:%M") if v else "—"


def _vehicle_label(name):
	if not name:
		return "—"
	v = frappe.db.get_value(
		"Vehicle", name,
		["custom_make", "make", "model", "custom_model", "custom_plate", "license_plate"],
		as_dict=True,
	)
	if not v:
		return name
	label = v.custom_model or " ".join(x for x in (v.custom_make or v.make, v.model) if x)
	plate = v.custom_plate or v.license_plate
	return f"{label} ({plate})" if label and plate else (label or plate or name)


def _employee_name(emp):
	return (frappe.db.get_value("Employee", emp, "employee_name") if emp else None) or emp or "—"


def get_context(context):
	require_login(context)
	fd = frappe.form_dict
	context.printed_on = now_datetime().strftime("%d %b %Y %H:%M")
	context.printed_by = (
		frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	)

	if fd.get("jobcard"):
		_jobcard(context, fd.get("jobcard").strip())
	elif fd.get("invoice"):
		_invoice(context, fd.get("invoice").strip())
	elif fd.get("receipt"):
		_receipt(context, fd.get("receipt").strip())
	elif fd.get("statement"):
		_statement(context, fd.get("statement").strip())
	elif fd.get("dayplan"):
		_dayplan(context, fd.get("dayplan").strip())
	elif fd.get("workorder"):
		_workorder(context, fd.get("workorder").strip())
	elif fd.get("complaints"):
		_complaints(context)
	elif fd.get("calls"):
		_calls(context, fd.get("calls").strip())
	else:
		context.mode = "none"
		context.title = "Print"
	return context


# ------------------------------------------------------------------- job card


def _jobcard(context, name):
	if not frappe.db.exists("Workshop Job Card", name):
		context.mode = "none"
		context.title = "Print"
		return
	doc = frappe.get_doc("Workshop Job Card", name)
	context.mode = "jobcard"
	context.title = f"Job Card {name}"

	services = []
	for s in doc.get("service_items") or []:
		services.append({
			"jobtype": s.jobtype or "—",
			"service": s.service or s.description or "—",
			"technician": _employee_name(s.technician),
			"hours": flt(s.hours),
		})
	complaints = [
		{"complaint": c.complaint or "—", "severity": c.get("severity") or "—", "notes": c.get("notes") or ""}
		for c in (doc.get("complaints") or [])
	]
	context.jc = {
		"name": doc.name,
		"status": doc.status or "Open",
		"customer": (
			frappe.db.get_value("Customer", doc.customer, "customer_name") if doc.customer else None
		) or doc.customer or "—",
		"mobile": doc.mobile_no or "—",
		"vehicle": _vehicle_label(doc.vehicle),
		"booking_date": _fmt_date(doc.booking_date),
		"promised": _fmt_date(doc.promised_delivery),
		"advisor": _employee_name(doc.service_advisor),
		"branch": doc.get("branch") or "—",
		"readings": {
			"odometer": cint(doc.reading_odometer),
			"next_km": cint(doc.next_service_km),
			"fuel": doc.fuel_level,
			"oil": doc.oil_level,
			"coolant": doc.coolant_level or "—",
			"battery": doc.battery_voltage,
			"tyre": doc.tyre_condition or "—",
			"spare": cint(doc.spare_tyre),
		},
		"body_condition": doc.body_condition or "",
		"services": services,
		"complaints": complaints,
		"photos": [
			{"image": p.image, "caption": p.caption or ""}
			for p in (doc.get("vehicle_photos") or []) if p.image
		],
		"billing_total": flt(doc.billing_total),
	}


# ---------------------------------------------------------- invoice / receipt


def _invoice(context, name):
	if not frappe.db.exists("Sales Invoice", name):
		context.mode = "none"
		context.title = "Print"
		return
	doc = frappe.get_doc("Sales Invoice", name)
	context.mode = "invoice"
	context.title = f"Invoice {name}"
	from frappe.utils import money_in_words

	context.inv = {
		"name": doc.name,
		"status": doc.status,
		"draft": doc.docstatus == 0,
		"customer": doc.customer_name or doc.customer,
		"posting_date": _fmt_date(doc.posting_date),
		"due_date": _fmt_date(doc.due_date),
		"items": [
			{"item": i.item_name or i.item_code, "description": (i.description or "")[:140],
			 "qty": flt(i.qty), "uom": i.uom or "", "rate": flt(i.rate), "amount": flt(i.amount)}
			for i in (doc.items or [])
		],
		"taxes": [
			{"description": t.description or t.account_head, "amount": flt(t.tax_amount)}
			for t in (doc.get("taxes") or []) if flt(t.tax_amount)
		],
		"net_total": flt(doc.net_total),
		"grand_total": flt(doc.grand_total),
		"outstanding": flt(doc.outstanding_amount),
		"in_words": money_in_words(flt(doc.grand_total), doc.currency or "AED"),
		"remarks": doc.get("remarks") or "",
	}


def _receipt(context, name):
	if not frappe.db.exists("Payment Entry", name):
		context.mode = "none"
		context.title = "Print"
		return
	doc = frappe.get_doc("Payment Entry", name)
	context.mode = "receipt"
	context.title = f"Receipt {name}"
	from frappe.utils import money_in_words

	context.pe = {
		"name": doc.name,
		"draft": doc.docstatus == 0,
		"party": doc.party_name or doc.party,
		"posting_date": _fmt_date(doc.posting_date),
		"mode": doc.mode_of_payment or "—",
		"paid_amount": flt(doc.paid_amount),
		"in_words": money_in_words(flt(doc.paid_amount), doc.paid_to_account_currency or "AED"),
		"reference_no": doc.reference_no or "—",
		"reference_date": _fmt_date(doc.reference_date),
		"references": [
			{"doctype": r.reference_doctype, "name": r.reference_name, "allocated": flt(r.allocated_amount)}
			for r in (doc.get("references") or [])
		],
		"received_by": context.printed_by,
	}


# ------------------------------------------------------------------ statement


def _statement(context, customer):
	if not frappe.db.exists("Customer", customer):
		context.mode = "none"
		context.title = "Print"
		return
	info = frappe.db.get_value(
		"Customer", customer, ["customer_name", "mobile_no", "email_id"], as_dict=True
	) or frappe._dict()
	context.mode = "statement"
	context.title = f"Statement — {info.customer_name or customer}"

	job_cards = frappe.get_all(
		"Workshop Job Card",
		filters={"customer": customer},
		fields=["name", "booking_date", "vehicle", "status", "billing_total", "creation"],
		order_by="creation desc", limit_page_length=100,
	)
	for j in job_cards:
		j["date"] = _fmt_date(j.booking_date or j.creation)
		j["vehicle_label"] = _vehicle_label(j.vehicle)

	invoices = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": ["<", 2]},
		fields=["name", "posting_date", "status", "grand_total", "outstanding_amount", "docstatus"],
		order_by="posting_date desc", limit_page_length=100,
	)
	for i in invoices:
		i["date"] = _fmt_date(i.posting_date)

	payments = frappe.get_all(
		"Payment Entry",
		filters={"party_type": "Customer", "party": customer, "docstatus": ["<", 2]},
		fields=["name", "posting_date", "mode_of_payment", "paid_amount", "docstatus"],
		order_by="posting_date desc", limit_page_length=100,
	)
	for p in payments:
		p["date"] = _fmt_date(p.posting_date)

	vehicles = frappe.get_all(
		"Vehicle", filters={"custom_customer": customer},
		fields=["name", "custom_model", "model", "custom_plate", "license_plate"],
		limit_page_length=100,
	)

	context.st = {
		"customer": info.customer_name or customer,
		"mobile": info.mobile_no or "—",
		"email": info.email_id or "—",
		"job_cards": job_cards,
		"invoices": invoices,
		"payments": payments,
		"vehicles": [
			{"label": v.custom_model or v.model or v.name, "plate": v.custom_plate or v.license_plate or v.name}
			for v in vehicles
		],
		"total_billed": sum(flt(i.grand_total) for i in invoices if i.docstatus == 1),
		"total_outstanding": sum(flt(i.outstanding_amount) for i in invoices if i.docstatus == 1),
		"total_paid": sum(flt(p.paid_amount) for p in payments if p.docstatus == 1),
		"jc_total": sum(flt(j.billing_total) for j in job_cards),
	}


# -------------------------------------------------------------------- dayplan


def _dayplan(context, date_arg):
	date = nowdate() if date_arg in ("", "today") else str(getdate(date_arg))
	context.mode = "dayplan"
	context.title = f"Day Sheet {_fmt_date(date)}"
	context.day = _fmt_date(date)
	# Same read the Daily Planner page uses -- open tasks grouped by priority.
	from garagedesk.api.daily_planner import get_today_task_groups

	groups = get_today_task_groups()
	# Enrich with vehicle / technician labels where the custom fields exist.
	meta = frappe.get_meta("Task")
	has_vehicle = meta.has_field("custom_vehicle")
	has_tech = meta.has_field("custom_technician")
	for g in groups:
		for t in g.get("tasks") or []:
			extra = frappe.db.get_value(
				"Task", t["name"],
				[f for f in ("custom_vehicle" if has_vehicle else None,
				             "custom_technician" if has_tech else None,
				             "exp_start_date") if f],
				as_dict=True,
			) or frappe._dict()
			t["vehicle"] = _vehicle_label(extra.get("custom_vehicle")) if extra.get("custom_vehicle") else "—"
			t["technician"] = _employee_name(extra.get("custom_technician")) if extra.get("custom_technician") else "—"
			t["due"] = _fmt_date(extra.get("exp_start_date")) if extra.get("exp_start_date") else "—"
	context.groups = groups
	context.total_tasks = sum(g.get("count") or 0 for g in groups)


# ------------------------------------------------------------------ workorder


def _workorder(context, name):
	if not frappe.db.exists("Work Order", name):
		context.mode = "none"
		context.title = "Print"
		return
	doc = frappe.get_doc("Work Order", name)
	context.mode = "workorder"
	context.title = f"Traveler {name}"
	context.wo = {
		"name": doc.name,
		"item": doc.item_name or doc.production_item,
		"qty": flt(doc.qty),
		"status": doc.status,
		"stage": doc.get("custom_production_stage") or "—",
		"bom": doc.bom_no or "—",
		"planned_start": _fmt_date(doc.planned_start_date),
		"delivery": _fmt_date(doc.get("expected_delivery_date")),
		"wip": doc.wip_warehouse or "—",
		"fg": doc.fg_warehouse or "—",
		"materials": [
			{"item": r.item_name or r.item_code, "qty": flt(r.required_qty),
			 "warehouse": r.source_warehouse or "—"}
			for r in (doc.get("required_items") or [])
		],
		"operations": [
			{"operation": o.operation, "workstation": o.workstation or "—",
			 "mins": flt(o.time_in_mins), "status": o.get("status") or "—"}
			for o in (doc.get("operations") or [])
		],
		"history": [
			{"stage": h.stage, "from_stage": h.from_stage or "—",
			 "entered_on": _fmt_dt(h.entered_on), "entered_by": h.entered_by or "—",
			 "hours": flt(h.duration_hours), "notes": h.notes or ""}
			for h in (doc.get("custom_stage_history") or [])
		],
	}


# ----------------------------------------------------------------- complaints


def _complaints(context):
	context.mode = "complaints"
	context.title = "Complaints Register"
	rows = frappe.get_all(
		"Workshop Job Card Complaint",
		fields=["parent", "complaint", "severity", "notes", "technician", "creation"],
		filters={"parenttype": "Workshop Job Card"},
		order_by="creation desc", limit_page_length=200,
	)
	parents = {r.parent for r in rows}
	cards = {
		c.name: c
		for c in frappe.get_all(
			"Workshop Job Card",
			filters={"name": ["in", list(parents)]} if parents else {"name": ""},
			fields=["name", "customer", "vehicle", "booking_date", "status"],
		)
	}
	cust_names = {}
	for c in cards.values():
		if c.customer and c.customer not in cust_names:
			cust_names[c.customer] = frappe.db.get_value("Customer", c.customer, "customer_name") or c.customer
	out = []
	for r in rows:
		card = cards.get(r.parent) or frappe._dict()
		out.append({
			"date": _fmt_date(card.booking_date or r.creation),
			"job_card": r.parent,
			"customer": cust_names.get(card.customer, card.customer or "—"),
			"vehicle": _vehicle_label(card.vehicle),
			"complaint": r.complaint or "—",
			"severity": r.severity or "—",
			"technician": _employee_name(r.technician),
			"jc_status": card.status or "—",
		})
	context.complaint_rows = out


# ---------------------------------------------------------------------- calls


def _calls(context, date_arg):
	date = nowdate() if date_arg in ("", "today") else str(getdate(date_arg))
	context.mode = "calls"
	context.title = f"Call List {_fmt_date(date)}"
	context.day = _fmt_date(date)
	rows = frappe.get_all(
		"Call Log",
		filters={"called_at": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]},
		fields=["name", "customer", "mobile_no", "direction", "status", "outcome",
		        "purpose", "telecaller", "called_at", "call_notes"],
		order_by="called_at asc", limit_page_length=300,
	)
	if not rows:
		# fall back to calls created that day (scheduled but not yet dialled)
		rows = frappe.get_all(
			"Call Log",
			filters={"creation": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]},
			fields=["name", "customer", "mobile_no", "direction", "status", "outcome",
			        "purpose", "telecaller", "called_at", "call_notes"],
			order_by="creation asc", limit_page_length=300,
		)
	cust_names = {}
	for r in rows:
		if r.customer and r.customer not in cust_names:
			cust_names[r.customer] = frappe.db.get_value("Customer", r.customer, "customer_name") or r.customer
		r["customer_label"] = cust_names.get(r.customer, r.customer or "—")
		r["time"] = get_datetime(r.called_at).strftime("%H:%M") if r.called_at else "—"
	outcomes = {}
	for r in rows:
		key = r.outcome or "No outcome"
		outcomes[key] = outcomes.get(key, 0) + 1
	context.call_rows = rows
	context.call_outcomes = sorted(outcomes.items(), key=lambda kv: -kv[1])
