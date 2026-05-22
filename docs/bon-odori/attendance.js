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
  const ROLE_OPTIONS = ["調理", "会計", "搬入"];

  const data = window.BON_ODORI_DATA || {};
  const apiUrl = data.attendanceApiUrl || "";

  let fileResponses = [];

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
      role: ROLE_OPTIONS.includes(row.role) ? row.role : "",
      equipment: row.equipment || "",
      note: row.note || "",
      updatedAt: row.updatedAt || "",
    };
  }

  function mergeResponses() {
    const map = new Map();
    fileResponses.forEach((row) => {
      if (row && row.name) map.set(row.name.trim(), normalizeRow(row));
    });
    Object.values(loadLocalMap()).forEach((row) => {
      if (row && row.name) map.set(row.name.trim(), normalizeRow(row));
    });
    return [...map.values()].sort((a, b) =>
      (a.name || "").localeCompare(b.name || "", "ja")
    );
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

  function renderMatrix(responses) {
    if (!responses.length) {
      return `<p class="attendance-empty">まだ登録がありません。下のフォームから入力してください。</p>`;
    }

    const rows = responses
      .map(
        (row) => `
      <tr>
        <td><strong>${escapeHtml(row.name)}</strong></td>
        <td>${renderStatusBadge(row.day11)}</td>
        <td class="slot-cell">${escapeHtml(formatSlots(row.slots?.day11))}</td>
        <td>${renderStatusBadge(row.day12)}</td>
        <td class="slot-cell">${escapeHtml(formatSlots(row.slots?.day12))}</td>
        <td>${escapeHtml(row.role || "—")}</td>
        <td class="muted">${escapeHtml(row.updatedAt ? formatTime(row.updatedAt) : "—")}</td>
      </tr>
    `
      )
      .join("");

    return `
      <div class="table-wrap">
        <table class="attendance-table">
          <thead>
            <tr>
              <th>名前</th>
              <th>7/11</th>
              <th>7/11 時間枠</th>
              <th>7/12</th>
              <th>7/12 時間枠</th>
              <th>担当</th>
              <th>更新</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
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
    document.getElementById("attendance-summary").innerHTML = renderSummary(responses);
    document.getElementById("attendance-matrix").innerHTML = renderMatrix(responses);
  }

  function upsertLocal(row) {
    const map = loadLocalMap();
    map[row.name] = row;
    saveLocalMap(map);
  }

  async function postToApi(row) {
    if (!apiUrl) return null;
    const res = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(row),
      mode: "cors",
    });
    if (!res.ok) throw new Error("API error");
    return res.json().catch(() => ({}));
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
        if (apiUrl) await postToApi(row);
        statusEl.textContent = `${row.name} さんの回答を保存しました。`;
        statusEl.className = "form-status ok";
        refreshView();
      } catch {
        statusEl.textContent =
          "この端末には保存しました。共有APIへの送信に失敗した場合は、エクスポートを坂倉または竹山家へ送ってください。";
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
    loadFileResponses().finally(() => {
      bindForm();
      bindTools();
      refreshView();
    });
  });
})();
