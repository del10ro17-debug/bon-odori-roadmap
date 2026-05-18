const data = window.WANGAN_PRICE_DASHBOARD_DATA || { observations: [] };
const observations = Array.isArray(data.observations) ? data.observations : [];

const filters = {
  area: document.getElementById("areaFilter"),
  project: document.getElementById("projectFilter"),
  priceType: document.getElementById("priceTypeFilter"),
  month: document.getElementById("monthFilter"),
  sizeBand: document.getElementById("sizeBandFilter"),
  room: document.getElementById("roomFilter"),
  direction: document.getElementById("directionFilter"),
  reduction: document.getElementById("reductionFilter"),
  minSize: document.getElementById("minSizeFilter"),
  maxSize: document.getElementById("maxSizeFilter"),
  maxUnit: document.getElementById("maxUnitFilter"),
  maxPrice: document.getElementById("maxPriceFilter"),
};

const elements = {
  summaryGrid: document.getElementById("summaryGrid"),
  insightGrid: document.getElementById("insightGrid"),
  areaRows: document.getElementById("areaRows"),
  projectRows: document.getElementById("projectRows"),
  bargainRows: document.getElementById("bargainRows"),
  rows: document.getElementById("observationRows"),
  emptyState: document.getElementById("emptyState"),
  tableWrap: document.getElementById("tableWrap"),
  generatedAt: document.getElementById("generatedAt"),
  resetFilters: document.getElementById("resetFilters"),
  exportCsv: document.getElementById("exportCsv"),
};

const charts = {
  scatter: document.getElementById("scatterChart"),
  area: document.getElementById("areaChart"),
  project: document.getElementById("projectChart"),
  size: document.getElementById("sizeChart"),
  monthly: document.getElementById("monthlyChart"),
  reduction: document.getElementById("reductionChart"),
};

const priceTypeLabels = {
  listing: "新着/売出",
  reduction: "値下げ",
  contract: "成約",
  revision: "価格改定",
};

let filteredRows = [];

function init() {
  elements.generatedAt.textContent = data.generatedAt
    ? `Generated: ${formatDateTime(data.generatedAt)} / ${observations.length.toLocaleString()} rows`
    : `No generated data / ${observations.length.toLocaleString()} rows`;

  populateFilter(filters.area, uniqueValues(observations, "area"));
  populateFilter(filters.project, uniqueValues(observations, "projectName"));
  populateFilter(filters.priceType, uniqueValues(observations, "priceType").map((value) => [value, priceTypeLabel(value)]));
  populateFilter(filters.month, uniqueValues(observations, "observedMonth"));
  populateFilter(filters.sizeBand, data.sizeBands || uniqueValues(observations, "sizeBand"));
  populateFilter(filters.room, uniqueValues(observations, "roomType"));
  populateFilter(filters.direction, uniqueValues(observations, "direction"));

  Object.values(filters).forEach((element) => element.addEventListener("input", render));
  elements.resetFilters.addEventListener("click", resetFilters);
  elements.exportCsv.addEventListener("click", exportVisibleCsv);
  render();
}

function populateFilter(select, values) {
  select.innerHTML = "";
  select.append(new Option("すべて", ""));
  values.forEach((value) => {
    if (Array.isArray(value)) select.append(new Option(value[1], value[0]));
    else select.append(new Option(value, value));
  });
}

function render() {
  filteredRows = observations.filter(matchesFilters);
  renderSummary(filteredRows);
  renderInsights(filteredRows);
  renderCharts(filteredRows);
  renderAreaTable(filteredRows);
  renderProjectTable(filteredRows);
  renderBargainTable(filteredRows);
  renderTable(filteredRows);
}

function matchesFilters(row) {
  if (filters.area.value && row.area !== filters.area.value) return false;
  if (filters.project.value && row.projectName !== filters.project.value) return false;
  if (filters.priceType.value && row.priceType !== filters.priceType.value) return false;
  if (filters.month.value && row.observedMonth !== filters.month.value) return false;
  if (filters.sizeBand.value && row.sizeBand !== filters.sizeBand.value) return false;
  if (filters.room.value && row.roomType !== filters.room.value) return false;
  if (filters.direction.value && row.direction !== filters.direction.value) return false;
  if (filters.reduction.value === "yes" && !(numberValue(row.priceChangeJpy) < 0)) return false;

  const size = numberValue(row.sizeSqm);
  const priceOku = numberValue(row.priceJpy) ? row.priceJpy / 100000000 : null;
  const unit = numberValue(row.unitPricePerTsuboMan);
  const minSize = numberValue(filters.minSize.value);
  const maxSize = numberValue(filters.maxSize.value);
  const maxUnit = numberValue(filters.maxUnit.value);
  const maxPrice = numberValue(filters.maxPrice.value);

  if (minSize !== null && (size === null || size < minSize)) return false;
  if (maxSize !== null && (size === null || size > maxSize)) return false;
  if (maxUnit !== null && (unit === null || unit > maxUnit)) return false;
  if (maxPrice !== null && (priceOku === null || priceOku > maxPrice)) return false;
  return true;
}

function renderSummary(rows) {
  const prices = numericValues(rows, "priceJpy");
  const unitPrices = numericValues(rows, "unitPricePerTsuboMan");
  const decreases = rows.filter((row) => numberValue(row.priceChangeJpy) < 0);
  const contracts = rows.filter((row) => row.priceType === "contract");
  const latestObservedAt = rows.map((row) => row.observedAt).filter(Boolean).sort().at(-1);

  const summary = [
    ["観測件数", rows.length.toLocaleString(), "フィルタ後の件数"],
    ["価格中央値", formatOku(median(prices)), "売出/成約混在。種別で絞込可"],
    ["坪単価中央値", formatTsubo(median(unitPrices)), "万円/坪"],
    ["値下げ件数", decreases.length.toLocaleString(), rows.length ? `${formatPercent(decreases.length / rows.length)} of rows` : "-"],
    ["成約件数", contracts.length.toLocaleString(), "成約事例として抽出"],
    ["最新観測日", latestObservedAt ? formatDate(latestObservedAt) : "-", "データ上の最新日"],
  ];

  elements.summaryGrid.innerHTML = summary.map(([label, value, note]) => `
    <div class="stat"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><span>${escapeHtml(note)}</span></div>
  `).join("");
}

function renderInsights(rows) {
  const areas = groupedStats(rows, "area").sort((a, b) => b.count - a.count);
  const reductions = rows.filter((row) => numberValue(row.priceChangeJpy) < 0);
  const bargains = rows.filter((row) => numberValue(row.bargainScore) !== null).sort((a, b) => b.bargainScore - a.bargainScore);
  const topArea = areas[0];
  const topReduction = reductions.sort((a, b) => Math.abs(b.priceChangeJpy) - Math.abs(a.priceChangeJpy))[0];
  const topBargain = bargains[0];

  const cards = [
    ["取引量の多いエリア", topArea ? `${topArea.label} ${topArea.count}件` : "-", topArea ? `坪単価中央値 ${formatTsubo(topArea.unitMedian)}` : "-"],
    ["最大値下げ", topReduction ? `${topReduction.projectName}` : "-", topReduction ? `${formatPriceChange(topReduction.priceChangeJpy)} / ${topReduction.area}` : "-"],
    ["買い得候補", topBargain ? `${topBargain.projectName}` : "-", topBargain ? `Score ${formatNumber(topBargain.bargainScore, 1)} / ${formatTsubo(topBargain.unitPricePerTsuboMan)}` : "-"],
  ];

  elements.insightGrid.innerHTML = cards.map(([label, value, note]) => `
    <div class="insight"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(label)}</span><p class="muted">${escapeHtml(note)}</p></div>
  `).join("");
}

function renderCharts(rows) {
  drawScatter(charts.scatter, rows);
  drawBars(charts.area, groupedStats(rows, "area").map((row) => ({ label: row.label, value: row.unitMedian })), { suffix: "万/坪" });
  drawBars(charts.project, groupedStats(rows, "projectName").map((row) => ({ label: row.label, value: row.unitMedian })), { suffix: "万/坪", limit: 10 });
  drawBars(charts.size, countBy(rows, (row) => row.sizeBand), { suffix: "件", sortLabel: true });
  drawBars(charts.monthly, countBy(rows, (row) => row.observedMonth), { suffix: "件", sortLabel: true });
  drawBars(charts.reduction, rows
    .filter((row) => numberValue(row.priceChangeJpy) < 0)
    .map((row) => ({ label: truncate(row.projectName || row.area || "-", 18), value: Math.abs(row.priceChangeJpy) / 10000 }))
    .sort((a, b) => b.value - a.value), { suffix: "万円", limit: 10 });
}

function renderAreaTable(rows) {
  elements.areaRows.innerHTML = groupedStats(rows, "area").map((row) => `
    <tr><td>${escapeHtml(row.label)}</td><td>${row.count.toLocaleString()}</td><td>${formatOku(row.priceMedian)}</td><td>${formatTsubo(row.unitMedian)}</td><td>${row.reductionCount.toLocaleString()}</td><td>${formatPercent(row.reductionShare)}</td></tr>
  `).join("");
}

function renderProjectTable(rows) {
  elements.projectRows.innerHTML = groupedStats(rows, "projectName")
    .filter((row) => row.count >= 2)
    .slice(0, 80)
    .map((row) => `
      <tr><td>${escapeHtml(row.label)}</td><td>${escapeHtml(row.area || "-")}</td><td>${row.count.toLocaleString()}</td><td>${formatOku(row.priceMedian)}</td><td>${formatTsubo(row.unitMedian)}</td><td>${row.reductionCount.toLocaleString()}</td><td>${formatDate(row.latestObservedAt)}</td></tr>
    `).join("");
}

function renderBargainTable(rows) {
  elements.bargainRows.innerHTML = rows
    .filter((row) => numberValue(row.bargainScore) !== null)
    .sort((a, b) => b.bargainScore - a.bargainScore)
    .slice(0, 80)
    .map((row) => `
      <tr><td>${formatNumber(row.bargainScore, 1)}</td><td>${escapeHtml(row.area || "-")}</td><td>${escapeHtml(row.projectName || "-")}</td><td>${formatFloor(row.floor)}</td><td>${formatSqm(row.sizeSqm)}</td><td>${escapeHtml(row.roomType || "-")}</td><td>${formatOku(row.priceJpy)}</td><td>${formatTsubo(row.unitPricePerTsuboMan)}</td><td class="${classForChange(row.priceChangeJpy)}">${formatPriceChange(row.priceChangeJpy)}</td><td>${formatPercent(row.discountToAreaMedianPct)}</td></tr>
    `).join("");
}

function renderTable(rows) {
  elements.emptyState.hidden = rows.length > 0;
  elements.tableWrap.hidden = rows.length === 0;

  elements.rows.innerHTML = rows.slice(0, 700).map((row) => `
    <tr>
      <td>${escapeHtml(formatDate(row.observedAt))}</td>
      <td>${escapeHtml(priceTypeLabel(row.priceType))}</td>
      <td>${escapeHtml(row.area || "-")}</td>
      <td>${escapeHtml(row.projectName || "-")}</td>
      <td>${escapeHtml(formatFloor(row.floor))}</td>
      <td>${escapeHtml(row.roomType || "-")}</td>
      <td>${escapeHtml(formatSqm(row.sizeSqm))}</td>
      <td>${escapeHtml(formatOku(row.priceJpy))}</td>
      <td>${escapeHtml(formatTsubo(row.unitPricePerTsuboMan))}</td>
      <td class="${classForChange(row.priceChangeJpy)}">${escapeHtml(formatPriceChange(row.priceChangeJpy))}</td>
      <td>${escapeHtml(row.direction || "-")}</td>
      <td title="${escapeHtml(row.sourceExcerpt || "")}">${escapeHtml(row.sourceExcerpt || "-")}</td>
    </tr>
  `).join("");
}

function drawScatter(canvas, rows) {
  const points = rows
    .map((row) => ({
      x: numberValue(row.sizeSqm),
      y: numberValue(row.priceJpy) ? row.priceJpy / 100000000 : null,
      label: `${row.projectName || "-"} ${row.villageName || ""} ${row.buildingCode || ""}`,
    }))
    .filter((point) => isNumber(point.x) && isNumber(point.y));

  const context = prepareCanvas(canvas);
  const { width, height } = canvas;
  drawEmptyAxes(context, width, height, "㎡", "億円");
  if (!points.length) {
    drawNoData(context, width, height);
    return;
  }

  const bounds = chartBounds(points.map((point) => point.x), points.map((point) => point.y));
  points.forEach((point) => {
    const x = scale(point.x, bounds.xMin, bounds.xMax, 48, width - 18);
    const y = scale(point.y, bounds.yMin, bounds.yMax, height - 34, 18);
    context.beginPath();
    context.fillStyle = "#0f766e";
    context.arc(x, y, 4, 0, Math.PI * 2);
    context.fill();
  });
}

function drawBars(canvas, entries, options = {}) {
  const context = prepareCanvas(canvas);
  const { width, height } = canvas;
  const limit = options.limit || 8;
  const rows = entries
    .filter((entry) => entry.label && isNumber(numberValue(entry.value)))
    .sort((a, b) => options.sortLabel ? String(a.label).localeCompare(String(b.label), "ja") : b.value - a.value)
    .slice(0, limit);

  if (!rows.length) {
    drawNoData(context, width, height);
    return;
  }

  const left = 120;
  const right = 24;
  const top = 18;
  const rowHeight = Math.min(30, (height - top - 28) / rows.length);
  const maxValue = Math.max(...rows.map((row) => row.value));

  context.fillStyle = "#64748b";
  context.font = "12px sans-serif";
  rows.forEach((row, index) => {
    const y = top + index * rowHeight;
    const barWidth = scale(row.value, 0, maxValue, 0, width - left - right);
    context.fillStyle = "#334155";
    context.fillText(truncate(row.label, 16), 8, y + rowHeight * 0.68);
    context.fillStyle = "#2563eb";
    context.fillRect(left, y + 5, barWidth, Math.max(10, rowHeight - 10));
    context.fillStyle = "#0f172a";
    context.fillText(`${formatNumber(row.value, 1)}${options.suffix || ""}`, left + barWidth + 6, y + rowHeight * 0.68);
  });
}

function prepareCanvas(canvas) {
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, canvas.width, canvas.height);
  return context;
}

function drawEmptyAxes(context, width, height, xLabel, yLabel) {
  context.strokeStyle = "#cbd5e1";
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(42, 16);
  context.lineTo(42, height - 30);
  context.lineTo(width - 14, height - 30);
  context.stroke();
  context.fillStyle = "#64748b";
  context.font = "12px sans-serif";
  context.fillText(yLabel, 8, 16);
  context.fillText(xLabel, width - 34, height - 8);
}

function drawNoData(context, width, height) {
  context.fillStyle = "#64748b";
  context.font = "16px sans-serif";
  context.textAlign = "center";
  context.fillText("No data", width / 2, height / 2);
  context.textAlign = "left";
}

function medianBy(rows, labelKey, valueKey) {
  const grouped = new Map();
  rows.forEach((row) => {
    const label = row[labelKey] || "Unknown";
    const value = numberValue(row[valueKey]);
    if (!isNumber(value)) return;
    if (!grouped.has(label)) grouped.set(label, []);
    grouped.get(label).push(value);
  });
  return Array.from(grouped, ([label, values]) => ({ label, value: median(values) }));
}

function countBy(rows, keyFunc) {
  const grouped = new Map();
  rows.forEach((row) => {
    const label = keyFunc(row) || "Unknown";
    grouped.set(label, (grouped.get(label) || 0) + 1);
  });
  return Array.from(grouped, ([label, value]) => ({ label, value }));
}

function groupedStats(rows, key) {
  const grouped = new Map();
  rows.forEach((row) => {
    const label = row[key] || "Unknown";
    if (!grouped.has(label)) grouped.set(label, []);
    grouped.get(label).push(row);
  });
  return Array.from(grouped, ([label, groupRows]) => {
    const prices = numericValues(groupRows, "priceJpy");
    const units = numericValues(groupRows, "unitPricePerTsuboMan");
    const reductions = groupRows.filter((row) => numberValue(row.priceChangeJpy) < 0);
    const latestObservedAt = groupRows.map((row) => row.observedAt).filter(Boolean).sort().at(-1);
    const area = mostCommon(groupRows.map((row) => row.area).filter(Boolean));
    return {
      label,
      area,
      count: groupRows.length,
      priceMedian: median(prices),
      unitMedian: median(units),
      reductionCount: reductions.length,
      reductionShare: groupRows.length ? reductions.length / groupRows.length : null,
      latestObservedAt,
    };
  }).sort((a, b) => b.count - a.count);
}

function numericValues(rows, key) {
  return rows.map((row) => numberValue(row[key])).filter(isNumber);
}

function mostCommon(values) {
  const counts = new Map();
  values.forEach((value) => counts.set(value, (counts.get(value) || 0) + 1));
  return Array.from(counts.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] || null;
}

function resetFilters() {
  Object.values(filters).forEach((element) => {
    element.value = "";
  });
  render();
}

function exportVisibleCsv() {
  const headers = [
    "observedAt",
    "priceType",
    "area",
    "projectName",
    "floor",
    "roomType",
    "sizeSqm",
    "sizeBand",
    "priceJpy",
    "unitPricePerTsuboMan",
    "previousPriceJpy",
    "priceChangeJpy",
    "priceChangeRate",
    "discountToAreaMedianPct",
    "bargainScore",
    "direction",
  ];
  const csv = [headers.join(",")]
    .concat(filteredRows.map((row) => headers.map((key) => csvCell(row[key])).join(",")))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "wangan-price-dashboard.csv";
  anchor.click();
  URL.revokeObjectURL(url);
}

function uniqueValues(rows, key) {
  return Array.from(new Set(rows.map((row) => row[key]).filter(Boolean))).sort();
}

function median(values) {
  if (!values.length) return null;
  const sorted = values.slice().sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  if (sorted.length % 2) return sorted[middle];
  return (sorted[middle - 1] + sorted[middle]) / 2;
}

function chartBounds(xValues, yValues) {
  const xMin = Math.min(...xValues);
  const xMax = Math.max(...xValues);
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  return {
    xMin: xMin === xMax ? xMin - 1 : xMin,
    xMax: xMin === xMax ? xMax + 1 : xMax,
    yMin: yMin === yMax ? yMin - 1 : yMin,
    yMax: yMin === yMax ? yMax + 1 : yMax,
  };
}

function scale(value, min, max, outMin, outMax) {
  if (max === min) return (outMin + outMax) / 2;
  return outMin + ((value - min) / (max - min)) * (outMax - outMin);
}

function segmentKey(row) {
  return [row.projectName, row.villageName, row.buildingCode].filter(Boolean).join(" ") || "Unknown";
}

function monthKey(value) {
  return value ? String(value).slice(0, 7) : "Unknown";
}

function priceTypeLabel(value) {
  return priceTypeLabels[value] || value || "-";
}

function formatOku(value) {
  const number = numberValue(value);
  if (!isNumber(number)) return "-";
  return `${formatNumber(number / 100000000, 2)}億円`;
}

function formatTsubo(value) {
  const number = numberValue(value);
  if (!isNumber(number)) return "-";
  return `${formatNumber(number, 1)}万/坪`;
}

function formatSqm(value) {
  const number = numberValue(value);
  if (!isNumber(number)) return "-";
  return `${formatNumber(number, 1)}㎡`;
}

function formatFloor(value) {
  const number = numberValue(value);
  if (!isNumber(number)) return "-";
  return `${number}階`;
}

function formatPriceChange(value) {
  const number = numberValue(value);
  if (!isNumber(number) || number === 0) return "-";
  const sign = number > 0 ? "+" : "-";
  return `${sign}${formatOku(Math.abs(number))}`;
}

function formatPercent(value) {
  const number = numberValue(value);
  if (!isNumber(number)) return "-";
  return `${formatNumber(number * 100, 1)}%`;
}

function classForChange(value) {
  const number = numberValue(value);
  if (!isNumber(number) || number === 0) return "";
  return number < 0 ? "negative" : "positive";
}

function formatDate(value) {
  if (!value) return "-";
  return String(value).slice(0, 10);
}

function formatDateTime(value) {
  if (!value) return "-";
  return String(value).replace("T", " ").slice(0, 16);
}

function formatNumber(value, digits = 0) {
  const number = numberValue(value);
  if (!isNumber(number)) return "-";
  return number.toLocaleString("ja-JP", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function numberValue(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function isNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function truncate(value, length) {
  if (!value) return "";
  return value.length <= length ? value : `${value.slice(0, length - 1)}…`;
}

function csvCell(value) {
  if (value === null || value === undefined) return "";
  return `"${String(value).replaceAll('"', '""')}"`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

init();
