(function () {
  const STORAGE_KEY = "bon-odori-2026-attendance-v2";
  const STATUS = {
    yes: { label: "参加", className: "yes" },
    no: { label: "不可", className: "no" },
    maybe: { label: "未定", className: "maybe" },
  };

  const TIME_SLOTS = [
    { id: "11-12", label: "11時〜12時" },
    { id: "12-13", label: "12時〜13時" },
    { id: "13-14", label: "13時〜14時" },
    { id: "14-15", label: "14時〜15時" },
    { id: "15-16", label: "15時〜16時" },
    { id: "16-17", label: "16時〜17時" },
    { id: "17-18", label: "17時〜18時" },
    { id: "18-19", label: "18時〜19時" },
    { id: "19-20", label: "19時〜20時" },
    { id: "20-21", label: "20時〜21時" },
    { id: "21-22", label: "21時〜22時" },
  ];

  const SLOT_IDS = new Set(TIME_SLOTS.map((s) => s.id));
  const ROLE_OPTIONS = ["調理", "店頭業務", "子供のケア", "全般"];
  const LEGACY_ROLE_MAP = { 会計: "店頭業務", 搬入: "全般" };

  function normalizeRole(role) {
    const r = (role || "").trim();
    if (LEGACY_ROLE_MAP[r]) return LEGACY_ROLE_MAP[r];
    return ROLE_OPTIONS.includes(r) ? r : "";
  }
  const SHIFT_TARGET = 7;

  const data = window.BON_ODORI_DATA || {};
  const apiUrl = (data.attendanceApiUrl || "").trim();
  const syncKey = (data.attendanceSyncKey || "").trim();
  const githubRepo = data.attendanceGithubRepo || "del10ro17-debug/bon-odori-roadmap";
  const githubBranch = data.attendanceGithubBranch || "main";
  const githubPath = data.attendanceGithubPath || "docs/bon-odori/attendance.json";
  const githubToken = (data.attendanceGithubToken || "").trim();
  const WRITE_TOKEN_KEY = "bon-odori-gh-write-token";

  let fileResponses = [];
  let sharedResponses = [];
  let lastSyncAt = "";
  let pollTimer = null;
  const POLL_MS = 30000;

  function hasSharedRead() {
    return Boolean(apiUrl || githubRepo);
  }

  function getWriteToken() {
    return (localStorage.getItem(WRITE_TOKEN_KEY) || githubToken || "").trim();
  }

  function hasSharedWrite() {
    return Boolean(getWriteToken() || apiUrl);
  }

  function rawGithubUrl() {
    return `https://raw.githubusercontent.com/${githubRepo}/${githubBranch}/${githubPath}`;
  }

  function githubApiUrl() {
    return `https://api.github.com/repos/${githubRepo}/contents/${githubPath}`;
  }

  function githubHeaders(json) {
    const headers = {
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    };
    const token = getWriteToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    if (json) headers["Content-Type"] = "application/json";
    return headers;
  }

  function decodeGithubContent(content) {
    const binary = atob(String(content).replace(/\n/g, ""));
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    return new TextDecoder().decode(bytes);
  }

  function encodeGithubContent(text) {
    const bytes = new TextEncoder().encode(text);
    let binary = "";
    bytes.forEach((b) => {
      binary += String.fromCharCode(b);
    });
    return btoa(binary);
  }

  function upsertRowInPayload(payload, row) {
    const normalized = normalizeRow(row);
    if (!normalized.name) return payload;
    const list = Array.isArray(payload.responses) ? payload.responses : [];
    const idx = list.findIndex((r) => r && r.name === normalized.name);
    if (idx >= 0) {
      const prevAt = rowUpdatedAt(list[idx]);
      const nextAt = rowUpdatedAt(normalized);
      if (nextAt >= prevAt) list[idx] = normalized;
    } else {
      list.push(normalized);
    }
    payload.responses = list.sort((a, b) =>
      (a.name || "").localeCompare(b.name || "", "ja")
    );
    payload.updatedAt = new Date().toISOString();
    return payload;
  }

  function loadFileResponses() {
    return fetch("./attendance.json", { cache: "no-store" })
      .then((res) => (res.ok ? res.json() : { responses: [] }))
      .then((json) => {
        fileResponses = Array.isArray(json.responses) ? json.responses : [];
        return fileResponses;
      })
      .catch(() => {
        fileResponses = [];
        return fileResponses;
      });
  }

  function loadLocalMap() {
    try {
      const v2 = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      if (Object.keys(v2).length) return v2;
      const legacy = JSON.parse(localStorage.getItem("bon-odori-2026-attendance-v1") || "{}");
      return legacy;
    } catch {
      return {};
    }
  }

  function saveLocalMap(map) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
  }

  function normalizeSlotList(value) {
    if (!value) return [];
    if (Array.isArray(value)) {
      return value.filter((id) => SLOT_IDS.has(id));
    }
    if (typeof value === "string" && value.trim()) {
      return value
        .split(/[,、\s]+/)
        .map((part) => part.trim())
        .filter((id) => SLOT_IDS.has(id));
    }
    return [];
  }

  function normalizeRow(row) {
    const slots = row.slots && typeof row.slots === "object" ? row.slots : {};
    return {
      name: (row.name || "").trim(),
      day11: STATUS[row.day11] ? row.day11 : "maybe",
      day12: STATUS[row.day12] ? row.day12 : "maybe",
      slots: {
        day11: normalizeSlotList(slots.day11 ?? row.day11Slots),
        day12: normalizeSlotList(slots.day12 ?? row.day12Slots),
      },
      role: normalizeRole(row.role),
      equipment: row.equipment || "",
      note: row.note || "",
      updatedAt: row.updatedAt || "",
    };
  }

  function rowUpdatedAt(row) {
    const t = Date.parse(row?.updatedAt || "");
    return Number.isFinite(t) ? t : 0;
  }

  function mergeResponses() {
    const map = new Map();
    const upsert = (row) => {
      if (!row?.name) return;
      const key = row.name.trim();
      const next = normalizeRow(row);
      const prev = map.get(key);
      if (!prev || rowUpdatedAt(next) >= rowUpdatedAt(prev)) {
        map.set(key, next);
      }
    };
    fileResponses.forEach(upsert);
    sharedResponses.forEach(upsert);
    Object.values(loadLocalMap()).forEach(upsert);
    return [...map.values()].sort((a, b) =>
      (a.name || "").localeCompare(b.name || "", "ja")
    );
  }

  function formatSyncTime(iso) {
    if (!iso) return "";
    try {
      return new Date(iso).toLocaleString("ja-JP", {
        month: "numeric",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  }

  function updateSyncStatus(state, detail) {
    const el = document.getElementById("att-sync-status");
    if (!el) return;
    if (!hasSharedRead()) {
      el.textContent =
        "自動同期は未設定です。回答はこの端末のみ保存されます。";
      el.className = "form-status warn";
      return;
    }
    if (!hasSharedWrite()) {
      el.textContent =
        "いまは「見るだけ」共有です。誰かが保存した内容を全員に反映するには、坂倉さんが一度だけ共有の設定（約5分）を完了してください。詳細は docs/bon-odori/共有の始め方.md";
      el.className = "form-status warn";
      if (state === "ok") {
        const when = formatSyncTime(lastSyncAt);
        if (when) el.textContent += `（他の人の回答を取得 ${when}）`;
      }
      return;
    }
    if (state === "syncing") {
      el.textContent = detail || "クラウドと同期中…";
      el.className = "form-status";
      return;
    }
    if (state === "error") {
      el.textContent =
        detail ||
        "クラウド同期に失敗しました。この端末の保存は残っています。しばらくして再保存してください。";
      el.className = "form-status warn";
      return;
    }
    const when = formatSyncTime(lastSyncAt);
    el.textContent = when
      ? `自動共有: オン（回答を保存すると全員に反映・更新 ${when}）`
      : "自動共有: オン（回答を保存すると全員に反映）";
    el.className = "form-status ok";
  }

  function applySharedPayload(json) {
    if (!json || typeof json !== "object") return;
    if (Array.isArray(json.responses)) {
      sharedResponses = json.responses.map((row) => normalizeRow(row));
    }
    if (json.updatedAt) lastSyncAt = json.updatedAt;
  }

  async function loadGithubResponses() {
    const res = await fetch(`${rawGithubUrl()}?t=${Date.now()}`, {
      cache: "no-store",
      method: "GET",
    });
    if (!res.ok) throw new Error(`GitHub raw ${res.status}`);
    const json = await res.json();
    applySharedPayload(json);
    return sharedResponses;
  }

  async function loadApiResponses() {
    const res = await fetch(apiUrl, { cache: "no-store", method: "GET" });
    if (!res.ok) throw new Error(`GET ${res.status}`);
    const json = await res.json();
    applySharedPayload(json);
    return sharedResponses;
  }

  async function loadSharedResponses() {
    if (!hasSharedRead()) return sharedResponses;
    try {
      if (apiUrl) await loadApiResponses();
      else await loadGithubResponses();
      updateSyncStatus("ok");
    } catch (err) {
      updateSyncStatus("error");
    }
    return sharedResponses;
  }

  async function postToGithub(row) {
    if (!getWriteToken()) throw new Error("no github token");
    updateSyncStatus("syncing", "GitHub に保存中…（10〜30秒かかることがあります）");
    const getRes = await fetch(`${githubApiUrl()}?ref=${encodeURIComponent(githubBranch)}`, {
      headers: githubHeaders(),
    });
    if (!getRes.ok) throw new Error(`GitHub GET ${getRes.status}`);
    const file = await getRes.json();
    let payload = { updatedAt: new Date().toISOString(), responses: [] };
    if (file.content) {
      payload = JSON.parse(decodeGithubContent(file.content));
    }
    payload = upsertRowInPayload(payload, row);
    const body = {
      message: `Update attendance: ${row.name}`,
      content: encodeGithubContent(JSON.stringify(payload, null, 2)),
      branch: githubBranch,
    };
    if (file.sha) body.sha = file.sha;
    const putRes = await fetch(githubApiUrl(), {
      method: "PUT",
      headers: githubHeaders(true),
      body: JSON.stringify(body),
    });
    if (!putRes.ok) throw new Error(`GitHub PUT ${putRes.status}`);
    applySharedPayload(payload);
    updateSyncStatus("ok");
    return payload;
  }

  async function postToShared(row) {
    if (getWriteToken()) return postToGithub(row);
    if (apiUrl) return postToApi(row);
    throw new Error("shared write not configured");
  }

  function applySetupTokenFromUrl() {
    const params = new URLSearchParams(location.search);
    const token = params.get("setup_token");
    if (!token) return;
    localStorage.setItem(WRITE_TOKEN_KEY, token);
    params.delete("setup_token");
    const q = params.toString();
    history.replaceState({}, "", location.pathname + (q ? `?${q}` : "") + location.hash);
  }

  function bindTokenSetup() {
    const form = document.getElementById("attendance-form");
    if (!form || document.getElementById("att-token-setup") || getWriteToken()) return;
    const box = document.createElement("div");
    box.id = "att-token-setup";
    box.className = "slot-section";
    box.innerHTML = `
      <label>共有設定（この端末で初回のみ）</label>
      <p class="slot-hint">保存を全員に反映するには、坂倉さんが <code>open_bon_odori_sync_setup.command</code> 実行後に LINE で送るトークンを貼り付けて「保存」してください。入れた端末だけ書き込みできます。</p>
      <input type="password" id="att-token-input" placeholder="トークンを貼り付け" style="width:100%;padding:10px;margin-bottom:8px;">
      <button type="button" class="btn-secondary" id="att-token-save">トークンをこの端末に保存</button>
      <p class="form-status" id="att-token-status"></p>
    `;
    form.parentElement.insertBefore(box, form);
    document.getElementById("att-token-save").addEventListener("click", () => {
      const status = document.getElementById("att-token-status");
      const value = document.getElementById("att-token-input").value.trim();
      if (!value) {
        status.textContent = "トークンを入力してください。";
        status.className = "form-status error";
        return;
      }
      localStorage.setItem(WRITE_TOKEN_KEY, value);
      status.textContent = "保存しました。この端末から回答を共有できます。";
      status.className = "form-status ok";
      updateSyncStatus("ok");
    });
  }

  function startPolling() {
    if (!hasSharedRead() || pollTimer) return;
    pollTimer = setInterval(() => {
      if (document.hidden) return;
      loadSharedResponses().then(() => refreshView());
    }, POLL_MS);
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) {
        loadSharedResponses().then(() => refreshView());
      }
    });
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function countByDay(responses, dayKey) {
    const counts = { yes: 0, no: 0, maybe: 0 };
    responses.forEach((row) => {
      const key = row[dayKey];
      if (counts[key] !== undefined) counts[key] += 1;
    });
    return counts;
  }

  function slotLabel(id) {
    return TIME_SLOTS.find((s) => s.id === id)?.label || id;
  }

  function formatSlots(slots) {
    if (!slots || !slots.length) return "—";
    return slots.map(slotLabel).join("、");
  }

  function isAvailableOnDay(row, dayKey) {
    return row[dayKey] !== "no";
  }

  function peopleForSlot(responses, dayKey, slotId) {
    return responses
      .filter((row) => isAvailableOnDay(row, dayKey))
      .filter((row) => (row.slots?.[dayKey] || []).includes(slotId))
      .sort((a, b) => (a.name || "").localeCompare(b.name || "", "ja"));
  }

  function countLevel(count) {
    if (count === 0) return 0;
    if (count <= 2) return 1;
    if (count < SHIFT_TARGET) return 2;
    return 3;
  }

  function renderScheduleWarnings(responses) {
    const warnings = [];
    responses.forEach((row) => {
      if (row.day11 !== "no" && !(row.slots?.day11 || []).length) {
        warnings.push(`${row.name} さん（7/11）: 参加または未定ですが時間枠未選択`);
      }
      if (row.day12 !== "no" && !(row.slots?.day12 || []).length) {
        warnings.push(`${row.name} さん（7/12）: 参加または未定ですが時間枠未選択`);
      }
    });
    if (!warnings.length) return "";
    return `
      <ul class="schedule-warnings">
        ${warnings.map((w) => `<li>${escapeHtml(w)}</li>`).join("")}
      </ul>
    `;
  }

  function slotIndices(slotIds) {
    return TIME_SLOTS.map((slot, index) => (slotIds.includes(slot.id) ? index : -1)).filter(
      (index) => index >= 0
    );
  }

  function mergeSlotRanges(indices) {
    if (!indices.length) return [];
    const ranges = [];
    let start = indices[0];
    let end = indices[0];
    for (let i = 1; i < indices.length; i += 1) {
      if (indices[i] === end + 1) {
        end = indices[i];
      } else {
        ranges.push({ start, end });
        start = indices[i];
        end = indices[i];
      }
    }
    ranges.push({ start, end });
    return ranges;
  }

  function rangeLabel(start, end) {
    const from = TIME_SLOTS[start].label.split("〜")[0];
    const to = TIME_SLOTS[end].label.split("〜")[1];
    return `${from}〜${to}`;
  }

  function renderGcalHourHead() {
    return TIME_SLOTS.map((slot) => {
      const hour = slot.id.split("-")[0];
      return `<div class="gcal-hour">${hour}</div>`;
    }).join("");
  }

  function renderGcalEventBar(row, dayKey) {
    const slots = row.slots?.[dayKey] || [];
    const ranges = mergeSlotRanges(slotIndices(slots));
    if (!ranges.length) return "";

    return ranges
      .map((range) => {
        const roleAttr = row.role ? ` data-role="${escapeHtml(row.role)}"` : "";
        return `
          <div class="gcal-event"${roleAttr}
            style="grid-column:${range.start + 1} / ${range.end + 2}"
            title="${escapeHtml(rangeLabel(range.start, range.end))}${row.role ? ` · ${row.role}` : ""}">
            ${escapeHtml(rangeLabel(range.start, range.end))}
          </div>
        `;
      })
      .join("");
  }

  function renderGcalPersonRow(row, dayKey) {
    if (row[dayKey] === "no") {
      return `
        <div class="gcal-row gcal-row-unavailable">
          <div class="gcal-name">
            <span>${escapeHtml(row.name)}</span>
            <span class="gcal-meta">${renderStatusBadge("no")}</span>
          </div>
          <div class="gcal-unavailable">この日は不可</div>
        </div>
      `;
    }

    const roleHtml = row.role
      ? `<span class="role-tag">${escapeHtml(row.role)}</span>`
      : "";
    const events = renderGcalEventBar(row, dayKey);
    const emptyHint = events
      ? ""
      : `<div class="gcal-event" style="grid-column:1/-1;opacity:0.55;background:#94a3b8">時間枠未選択</div>`;

    return `
      <div class="gcal-row">
        <div class="gcal-name">
          <span>${escapeHtml(row.name)}</span>
          <span class="gcal-meta">${renderStatusBadge(row[dayKey])}${roleHtml}</span>
        </div>
        <div class="gcal-track">
          ${events}${emptyHint}
        </div>
      </div>
    `;
  }

  function renderGcalHeatmapRow(responses, dayKey) {
    const cells = TIME_SLOTS.map((slot) => {
      const people = peopleForSlot(responses, dayKey, slot.id);
      const level = countLevel(people.length);
      return `
        <div class="gcal-heat-cell lv-${level}" title="${slot.label}">
          <span>${people.length}</span>
          <span style="font-size:9px;font-weight:500">名</span>
        </div>
      `;
    }).join("");

    return `
      <div class="gcal-heatmap-row">
        <div class="gcal-name"><span>合計</span><span class="gcal-meta" style="font-size:11px;font-weight:500;color:var(--muted)">人数/枠</span></div>
        ${cells}
      </div>
    `;
  }

  function renderGcalDayPanel(responses, dayKey, dayLabel) {
    const people = responses.filter((row) => row[dayKey] !== "no");
    if (!people.length) {
      return `
        <section class="gcal-day-panel" data-day="${dayKey}">
          <h4 class="gcal-day-title">${dayLabel}</h4>
          <p class="gcal-empty-day">この日に参加可能な登録はまだありません。</p>
        </section>
      `;
    }

    const rows = people.map((row) => renderGcalPersonRow(row, dayKey)).join("");

    return `
      <section class="gcal-day-panel" data-day="${dayKey}">
        <h4 class="gcal-day-title">${dayLabel}</h4>
        <div class="gcal-scroll">
          <div class="gcal-sheet">
            <div class="gcal-head">
              <div class="gcal-corner">名前</div>
              ${renderGcalHourHead()}
            </div>
            ${renderGcalHeatmapRow(responses, dayKey)}
            ${rows}
          </div>
        </div>
      </section>
    `;
  }

  function renderCalendarView(responses) {
    if (!responses.length) {
      return `<p class="attendance-empty">まだ登録がありません。下のフォームから入力してください。</p>`;
    }

    return `
      <div class="cal-day-tabs" role="tablist" aria-label="表示する日">
        <button type="button" class="cal-day-tab active" data-day="all" aria-selected="true">両日</button>
        <button type="button" class="cal-day-tab" data-day="day11" aria-selected="false">7/11（土）</button>
        <button type="button" class="cal-day-tab" data-day="day12" aria-selected="false">7/12（日）</button>
      </div>
      ${renderScheduleWarnings(responses)}
      ${renderGcalDayPanel(responses, "day11", "7/11（土）")}
      ${renderGcalDayPanel(responses, "day12", "7/12（日）")}
    `;
  }

  function renderScheduleBoard(responses) {
    if (!responses.length) {
      return `<p class="attendance-empty">回答があると、ここにスケジュール表が表示されます。</p>`;
    }

    const legend = `
      <div class="schedule-legend">
        <span><i class="lv-0"></i> 0名</span>
        <span><i class="lv-1"></i> 1〜2名</span>
        <span><i class="lv-2"></i> 3〜${SHIFT_TARGET - 1}名</span>
        <span><i class="lv-3"></i> ${SHIFT_TARGET}名以上（目安達成）</span>
      </div>
    `;

    return `
      ${legend}
      ${renderScheduleWarnings(responses)}
      <p class="schedule-note">各時間枠に入れる人数（シフト組みの参考）</p>
      ${renderGcalDayPanel(responses, "day11", "7/11（土）")}
      ${renderGcalDayPanel(responses, "day12", "7/12（日）")}
    `;
  }

  function renderStatusBadge(value) {
    const item = STATUS[value] || STATUS.maybe;
    return `<span class="status-badge ${item.className}">${item.label}</span>`;
  }

  function renderSummary(responses) {
    const c11 = countByDay(responses, "day11");
    const c12 = countByDay(responses, "day12");
    const bothYes = responses.filter((r) => r.day11 === "yes" && r.day12 === "yes").length;
    const target = data.staffing?.targetCount || 16;

    return `
      <div class="attendance-stats">
        <article class="attendance-stat">
          <h3>7/11（土）</h3>
          <p><strong class="num yes">${c11.yes}</strong> 参加 /
          <strong class="num no">${c11.no}</strong> 不可 /
          <strong class="num maybe">${c11.maybe}</strong> 未定</p>
        </article>
        <article class="attendance-stat">
          <h3>7/12（日）</h3>
          <p><strong class="num yes">${c12.yes}</strong> 参加 /
          <strong class="num no">${c12.no}</strong> 不可 /
          <strong class="num maybe">${c12.maybe}</strong> 未定</p>
        </article>
        <article class="attendance-stat">
          <h3>両日参加</h3>
          <p><strong class="num yes">${bothYes}</strong> 名</p>
        </article>
        <article class="attendance-stat">
          <h3>登録人数</h3>
          <p><strong class="num">${responses.length}</strong> / ${target} 名</p>
          <div class="progress-bar"><span style="width:${Math.min(100, (responses.length / target) * 100)}%"></span></div>
        </article>
      </div>
    `;
  }

  function bindCalendarDayTabs() {
    const root = document.getElementById("attendance-matrix");
    if (!root) return;

    const tabs = root.querySelectorAll(".cal-day-tab");
    const panels = root.querySelectorAll(".gcal-day-panel");

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const day = tab.dataset.day;
        tabs.forEach((btn) => {
          const on = btn === tab;
          btn.classList.toggle("active", on);
          btn.setAttribute("aria-selected", on ? "true" : "false");
        });
        panels.forEach((panel) => {
          if (day === "all") {
            panel.hidden = false;
          } else {
            panel.hidden = panel.dataset.day !== day;
          }
        });
      });
    });
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function formatTime(iso) {
    try {
      return new Date(iso).toLocaleString("ja-JP", {
        month: "numeric",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  }

  function refreshView() {
    const responses = mergeResponses();
    const scheduleHtml = renderScheduleBoard(responses);

    document.getElementById("attendance-summary").innerHTML = renderSummary(responses);

    const scheduleEl = document.getElementById("attendance-schedule");
    if (scheduleEl) scheduleEl.innerHTML = scheduleHtml;

    const scheduleTabEl = document.getElementById("schedule-availability");
    if (scheduleTabEl) scheduleTabEl.innerHTML = scheduleHtml;

    const matrixEl = document.getElementById("attendance-matrix");
    if (matrixEl) {
      matrixEl.innerHTML = renderCalendarView(responses);
      bindCalendarDayTabs();
    }
  }

  function upsertLocal(row) {
    const map = loadLocalMap();
    map[row.name] = row;
    saveLocalMap(map);
  }

  async function postToApi(row) {
    if (!apiUrl) return null;
    updateSyncStatus("syncing", "回答を共有中…");
    const payload = syncKey ? { syncKey, row } : row;
    const res = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      mode: "cors",
    });
    if (!res.ok) throw new Error(`POST ${res.status}`);
    const json = await res.json();
    applySharedPayload(json);
    updateSyncStatus("ok");
    return json;
  }

  function ensureSyncStatusEl() {
    const form = document.getElementById("attendance-form");
    if (!form || document.getElementById("att-sync-status")) return;
    const el = document.createElement("p");
    el.id = "att-sync-status";
    el.className = "form-status";
    form.parentElement.insertBefore(el, form);
  }

  function renderSlotGrid(dayKey) {
    return `
      <div class="slot-grid" data-day="${dayKey}">
        ${TIME_SLOTS.map(
          (slot) => `
          <label class="slot-chip">
            <input type="checkbox" name="slots-${dayKey}" value="${slot.id}">
            <span>${slot.label}</span>
          </label>
        `
        ).join("")}
      </div>
    `;
  }

  function readSlotsFromForm(form, dayKey) {
    return [...form.querySelectorAll(`input[name="slots-${dayKey}"]:checked`)].map(
      (el) => el.value
    );
  }

  function setSlotsOnForm(form, dayKey, slots) {
    const set = new Set(slots || []);
    form.querySelectorAll(`input[name="slots-${dayKey}"]`).forEach((el) => {
      el.checked = set.has(el.value);
    });
  }

  function bindForm() {
    const form = document.getElementById("attendance-form");
    const nameInput = document.getElementById("att-name");
    const nameSuggestions = document.getElementById("att-name-suggestions");
    const statusEl = document.getElementById("attendance-form-status");

    document.getElementById("att-slots-day11").innerHTML = renderSlotGrid("day11");
    document.getElementById("att-slots-day12").innerHTML = renderSlotGrid("day12");

    const uniqueNames = [...new Set((data.attendanceRoster || []).map((r) => r.name))];
    nameSuggestions.innerHTML = uniqueNames
      .map((n) => `<option value="${escapeHtml(n)}">`)
      .join("");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      statusEl.textContent = "保存中…";
      statusEl.className = "form-status";

      const row = normalizeRow({
        name: nameInput.value,
        day11: form.querySelector('input[name="day11"]:checked')?.value || "maybe",
        day12: form.querySelector('input[name="day12"]:checked')?.value || "maybe",
        slots: {
          day11: readSlotsFromForm(form, "day11"),
          day12: readSlotsFromForm(form, "day12"),
        },
        role: form.querySelector('input[name="role"]:checked')?.value || "",
        equipment: document.getElementById("att-equipment").value,
        note: document.getElementById("att-note").value,
        updatedAt: new Date().toISOString(),
      });

      if (!row.name) {
        statusEl.textContent = "名前を入力してください。";
        statusEl.className = "form-status error";
        return;
      }

      try {
        upsertLocal(row);
        if (hasSharedWrite()) {
          await postToShared(row);
          statusEl.textContent = `${row.name} さんの回答を保存しました。全員の画面に反映されます（30秒ほど）。`;
        } else {
          statusEl.textContent = `${row.name} さんの回答をこの端末に保存しました（共有の設定が終わると全員に見えます）。`;
        }
        statusEl.className = "form-status ok";
        refreshView();
      } catch {
        statusEl.textContent = hasSharedWrite()
          ? "保存に失敗しました。通信を確認して、もう一度「回答を保存」を押してください。"
          : "この端末には保存しました。全員に見せるには坂倉さんが共有の設定を完了する必要があります。";
        statusEl.className = "form-status warn";
        refreshView();
      }
    });

    nameInput.addEventListener("change", () => {
      const existing = mergeResponses().find((r) => r.name === nameInput.value.trim());
      if (!existing) return;
      form.querySelector(`input[name="day11"][value="${existing.day11}"]`)?.click();
      form.querySelector(`input[name="day12"][value="${existing.day12}"]`)?.click();
      setSlotsOnForm(form, "day11", existing.slots?.day11);
      setSlotsOnForm(form, "day12", existing.slots?.day12);
      form.querySelector(`input[name="role"][value="${existing.role}"]`)?.click();
      if (!existing.role) {
        const noneRole = form.querySelector('input[name="role"][value=""]');
        if (noneRole) noneRole.checked = true;
      }
      document.getElementById("att-equipment").value = existing.equipment || "";
      document.getElementById("att-note").value = existing.note || "";
    });
  }

  function bindTools() {
    const exportBtn = document.getElementById("att-export");
    const importBtn = document.getElementById("att-import");
    const importArea = document.getElementById("att-import-area");
    const toolStatus = document.getElementById("att-tool-status");

    exportBtn.addEventListener("click", () => {
      const payload = {
        updatedAt: new Date().toISOString(),
        responses: mergeResponses(),
      };
      const text = JSON.stringify(payload, null, 2);
      navigator.clipboard.writeText(text).then(
        () => {
          toolStatus.textContent =
            "JSONをクリップボードにコピーしました。坂倉または竹山家へLINEで送れます。";
          toolStatus.className = "form-status ok";
        },
        () => {
          toolStatus.textContent = "コピーに失敗しました。下のテキストを手動でコピーしてください。";
          importArea.value = text;
          importArea.hidden = false;
        }
      );
      importArea.value = text;
    });

    const importActions = document.getElementById("att-import-actions");

    importBtn.addEventListener("click", () => {
      const show = importArea.hidden;
      importArea.hidden = !show;
      importActions.hidden = !show;
      toolStatus.textContent = show
        ? "JSONを貼り付けて「取り込む」を押してください。"
        : "";
    });

    document.getElementById("att-import-run").addEventListener("click", () => {
      try {
        const json = JSON.parse(importArea.value || "{}");
        const list = Array.isArray(json) ? json : json.responses;
        if (!Array.isArray(list)) throw new Error("invalid");
        const map = loadLocalMap();
        list.forEach((row) => {
          const normalized = normalizeRow(row);
          if (normalized.name) map[normalized.name] = normalized;
        });
        saveLocalMap(map);
        toolStatus.textContent = `${list.length} 件を取り込みました。`;
        toolStatus.className = "form-status ok";
        refreshView();
      } catch {
        toolStatus.textContent = "JSONの形式が正しくありません。";
        toolStatus.className = "form-status error";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    applySetupTokenFromUrl();
    ensureSyncStatusEl();
    bindTokenSetup();
    updateSyncStatus(hasSharedRead() ? "syncing" : "off");
    Promise.all([loadFileResponses(), loadSharedResponses()])
      .finally(() => {
        bindForm();
        bindTools();
        refreshView();
        startPolling();
      });
  });
})();
