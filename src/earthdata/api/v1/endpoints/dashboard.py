"""Interactive HTML dashboard for visualising Earth observation data."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])

_DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>EarthData Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; margin: 2rem; }
  h1 { margin-bottom: 0.25rem; }
  .subtitle { color: #666; margin-top: 0; }
  .tiles { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1.5rem 0; }
  .tile { border: 1px solid #ccc; border-radius: 8px; padding: 1rem 1.5rem; min-width: 140px; }
  .tile .value { font-size: 1.75rem; font-weight: 600; }
  .tile .label { color: #666; font-size: 0.85rem; }
  .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
  .chart-card { border: 1px solid #ccc; border-radius: 8px; padding: 1rem; }
  @media (max-width: 900px) { .charts { grid-template-columns: 1fr; } }
  select { padding: 0.25rem 0.5rem; }
</style>
</head>
<body>
  <h1>EarthData Dashboard</h1>
  <p class="subtitle">Earth observation events ingested from NASA EONET.</p>

  <div class="tiles" id="tiles"></div>

  <div class="charts">
    <div class="chart-card">
      <h3>Events by category</h3>
      <canvas id="categoryChart"></canvas>
    </div>
    <div class="chart-card">
      <h3>Events over time
        <select id="intervalSelect">
          <option value="day">Daily</option>
          <option value="week">Weekly</option>
          <option value="month">Monthly</option>
        </select>
      </h3>
      <canvas id="timeseriesChart"></canvas>
    </div>
  </div>

  <script>
    const API_BASE = "/api/v1/analytics";

    function renderTiles(summary) {
      const tiles = document.getElementById("tiles");
      const items = [
        ["Total events", summary.total_count],
        ["Open", summary.open_count],
        ["Closed", summary.closed_count],
        ["Categories", summary.by_category.length],
      ];
      tiles.innerHTML = items
        .map(([label, value]) => `
          <div class="tile">
            <div class="value">${value}</div>
            <div class="label">${label}</div>
          </div>`)
        .join("");
    }

    let categoryChart;
    function renderCategoryChart(summary) {
      const ctx = document.getElementById("categoryChart");
      const labels = summary.by_category.map((row) => row.category);
      const data = summary.by_category.map((row) => row.count);
      if (categoryChart) categoryChart.destroy();
      categoryChart = new Chart(ctx, {
        type: "bar",
        data: { labels, datasets: [{ label: "Events", data, backgroundColor: "#4f8ef7" }] },
        options: { responsive: true, plugins: { legend: { display: false } } },
      });
    }

    let timeseriesChart;
    async function renderTimeseriesChart(interval) {
      const response = await fetch(`${API_BASE}/timeseries?interval=${interval}`);
      const body = await response.json();
      const labels = body.points.map((point) => point.bucket_start);
      const data = body.points.map((point) => point.count);
      const ctx = document.getElementById("timeseriesChart");
      if (timeseriesChart) timeseriesChart.destroy();
      timeseriesChart = new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [{ label: "Events", data, borderColor: "#f76c4f", tension: 0.25 }],
        },
        options: { responsive: true, plugins: { legend: { display: false } } },
      });
    }

    async function init() {
      const summaryResponse = await fetch(`${API_BASE}/summary`);
      const summary = await summaryResponse.json();
      renderTiles(summary);
      renderCategoryChart(summary);
      await renderTimeseriesChart("day");

      document.getElementById("intervalSelect").addEventListener("change", (event) => {
        renderTimeseriesChart(event.target.value);
      });
    }

    init();
  </script>
</body>
</html>
"""


@router.get(
    "/dashboard",
    response_class=HTMLResponse,
    summary="Interactive visualisation dashboard",
)
async def get_dashboard() -> HTMLResponse:
    """Serve the interactive HTML dashboard (charts fetch data client-side)."""
    return HTMLResponse(content=_DASHBOARD_HTML)
