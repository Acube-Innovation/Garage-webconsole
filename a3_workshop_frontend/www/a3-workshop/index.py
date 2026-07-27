import math

import frappe
from a3_workshop_frontend.website_utils import require_login

no_cache = 1

# --- Service Analytics bar chart geometry (matches the SVG's 560x240 viewBox) ---
CHART_BASELINE = 200  # y of the x-axis
CHART_TOP = 20  # y the tallest bar reaches
CHART_LEFT = 60  # x of the first bar
CHART_STEP = 70  # distance between bars
CHART_BAR_W = 40
GRID_LINES = 4  # horizontal gridlines above the baseline

# --- Vehicle Status donut geometry (matches the SVG's 220x200 viewBox) ---
DONUT_R = 70
DONUT_CIRCUMFERENCE = 2 * math.pi * DONUT_R


def _nice_ceiling(value):
	"""Smallest axis top >= `value` whose gridline step comes off the 1-2-5 ladder,
	so the labels stay whole numbers whatever the week's volume is (4, 8, 20, 40 …)."""
	if value <= 0:
		return GRID_LINES  # empty week — still draw a readable 0..4 axis
	exp = 0
	while True:
		for mult in (1, 2, 5):
			step = mult * (10 ** exp)
			if step * GRID_LINES >= value:
				return step * GRID_LINES
		exp += 1


def _bar_chart(analytics):
	"""Turn per-day counts into bar rectangles + gridlines for the SVG."""
	days = analytics.get("days") or []
	top = _nice_ceiling(max([d["count"] for d in days] or [0]))
	span = CHART_BASELINE - CHART_TOP

	bars = []
	for i, d in enumerate(days):
		height = (d["count"] / top) * span if top else 0
		bars.append({
			"label": d["label"],
			"count": d["count"],
			"x": CHART_LEFT + i * CHART_STEP,
			"y": CHART_BASELINE - height,
			"w": CHART_BAR_W,
			"h": height,
		})

	grid = []
	for i in range(GRID_LINES + 1):
		value = top * i // GRID_LINES
		grid.append({"value": value, "y": CHART_BASELINE - (value / top) * span if top else CHART_BASELINE})

	return {"bars": bars, "grid": grid, "total": analytics.get("total", 0)}


def _donut(status):
	"""Turn the vehicle split into stroke-dasharray/offset arcs for the SVG."""
	total = sum(s["count"] for s in status.get("segments") or []) or 0
	arcs, offset = [], 0.0
	for seg in status.get("segments") or []:
		length = (seg["count"] / total) * DONUT_CIRCUMFERENCE if total else 0
		arcs.append({
			"label": seg["label"],
			"color": seg["color"],
			"count": seg["count"],
			"dash": "{0:.2f} {1:.2f}".format(length, DONUT_CIRCUMFERENCE - length),
			"offset": "{0:.2f}".format(-offset),
			"pct": round(seg["count"] * 100.0 / total) if total else 0,
		})
		offset += length
	return {"arcs": arcs, "total": total, "circumference": round(DONUT_CIRCUMFERENCE, 2)}


def get_context(context):
	require_login(context)
	context.title = "Home"
	context.page_icon = "fa-gauge-high"
	context.subtitle = ""
	context.breadcrumb = ""

	from garagedesk.api.dashboard import (
		get_recent_job_cards,
		get_service_analytics,
		get_stat_tiles,
		get_vehicle_status,
	)

	context.tiles = get_stat_tiles()
	context.chart = _bar_chart(get_service_analytics())
	context.donut = _donut(get_vehicle_status())
	context.recent_job_cards = get_recent_job_cards()
	return context
