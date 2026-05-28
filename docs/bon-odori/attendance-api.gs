/**
 * 晴海盆踊り2026 — 参加可否の共有API（Google Apps Script）
 *
 * 1. script.google.com で新規プロジェクトを作成し、このファイルの内容を貼り付け
 * 2. エディタで setup() を1回実行（スプレッドシート作成・権限承認）
 * 3. デプロイ → 新しいデプロイ → 種類: ウェブアプリ
 *    - 実行ユーザー: 自分
 *    - アクセス: 全員
 * 4. 発行された URL を docs/bon-odori/data.js の attendanceApiUrl に設定して push
 *
 * 詳細: ATTENDANCE_SYNC.md
 */

const DATA_CELL = "A1";
const SHEET_NAME = "attendance";

function ensureStore_() {
  let id = PropertiesService.getScriptProperties().getProperty("SPREADSHEET_ID");
  if (!id) {
    setup();
    id = PropertiesService.getScriptProperties().getProperty("SPREADSHEET_ID");
  }
  return id;
}

function getStoreSheet_() {
  const id = ensureStore_();
  const ss = SpreadsheetApp.openById(id);
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.getRange(DATA_CELL).setValue("{}");
  }
  return sheet;
}

function loadData_() {
  const raw = getStoreSheet_().getRange(DATA_CELL).getValue();
  if (!raw) {
    return { updatedAt: new Date().toISOString(), responses: [] };
  }
  try {
    const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
    if (!parsed || typeof parsed !== "object") {
      return { updatedAt: new Date().toISOString(), responses: [] };
    }
    if (!Array.isArray(parsed.responses)) parsed.responses = [];
    return parsed;
  } catch (err) {
    return { updatedAt: new Date().toISOString(), responses: [] };
  }
}

function saveData_(data) {
  data.updatedAt = new Date().toISOString();
  getStoreSheet_().getRange(DATA_CELL).setValue(JSON.stringify(data));
  return data;
}

function normalizeRow_(row) {
  if (!row || !row.name) return null;
  const slots = row.slots && typeof row.slots === "object" ? row.slots : {};
  return {
    name: String(row.name).trim(),
    day11: row.day11 || "maybe",
    day12: row.day12 || "maybe",
    slots: {
      day11: Array.isArray(slots.day11) ? slots.day11 : [],
      day12: Array.isArray(slots.day12) ? slots.day12 : [],
    },
    role: row.role || "",
    equipment: row.equipment || "",
    note: row.note || "",
    updatedAt: row.updatedAt || new Date().toISOString(),
  };
}

function upsertRow_(data, row) {
  const normalized = normalizeRow_(row);
  if (!normalized) return data;
  const list = Array.isArray(data.responses) ? data.responses : [];
  const idx = list.findIndex((r) => r && r.name === normalized.name);
  if (idx >= 0) {
    const prev = list[idx];
    const prevAt = Date.parse(prev.updatedAt || "") || 0;
    const nextAt = Date.parse(normalized.updatedAt || "") || 0;
    if (nextAt >= prevAt) list[idx] = normalized;
  } else {
    list.push(normalized);
  }
  data.responses = list.sort((a, b) =>
    String(a.name).localeCompare(String(b.name), "ja")
  );
  return data;
}

function jsonOutput_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(
    ContentService.MimeType.JSON
  );
}

function productionResponses_() {
  return [
    {
      name: "坂倉 遥",
      day11: "yes",
      day12: "yes",
      slots: {
        day11: [
          "11-12",
          "12-13",
          "13-14",
          "14-15",
          "15-16",
          "16-17",
          "17-18",
          "18-19",
          "19-20",
          "20-21",
          "21-22",
        ],
        day12: [
          "11-12",
          "12-13",
          "13-14",
          "14-15",
          "15-16",
          "16-17",
          "17-18",
          "18-19",
          "19-20",
          "20-21",
          "21-22",
        ],
      },
      role: "",
      equipment: "",
      note: "",
      updatedAt: "2026-05-28T03:10:33.987Z",
    },
    {
      name: "坂倉 翔",
      day11: "yes",
      day12: "yes",
      slots: { day11: [], day12: [] },
      role: "",
      equipment: "",
      note: "",
      updatedAt: "2026-05-22T22:57:33.926Z",
    },
  ];
}

function resetProductionResponses_() {
  let data = { updatedAt: new Date().toISOString(), responses: [] };
  productionResponses_().forEach((row) => {
    data = upsertRow_(data, row);
  });
  return saveData_(data);
}

/** テスト用の名前を削除（エディタから1回実行） */
function cleanupTestResponses() {
  const testName = /テスト|CORS|POSTノーリダイレクト|^x$/i;
  let data = loadData_();
  const before = (data.responses || []).length;
  data.responses = (data.responses || []).filter(
    (r) => r && r.name && !testName.test(String(r.name).trim())
  );
  saveData_(data);
  Logger.log("cleanup: " + before + " -> " + data.responses.length);
}

function doGet(e) {
  const action = e && e.parameter ? e.parameter.action : "";
  const data = e && e.parameter ? e.parameter.data : "";
  if (action === "resetProduction") {
    return jsonOutput_(resetProductionResponses_());
  }
  if (action === "save" && data) {
    try {
      const row = JSON.parse(data);
      let store = loadData_();
      store = upsertRow_(store, row);
      store = saveData_(store);
      return jsonOutput_(store);
    } catch (err) {
      return jsonOutput_({
        ok: false,
        error: String(err),
        updatedAt: new Date().toISOString(),
        responses: [],
      });
    }
  }
  return jsonOutput_(loadData_());
}

function doPost(e) {
  try {
    const body = e && e.postData && e.postData.contents ? e.postData.contents : "{}";
    const parsed = JSON.parse(body);
    if (parsed && parsed.__reset && Array.isArray(parsed.responses)) {
      let data = { updatedAt: new Date().toISOString(), responses: [] };
      parsed.responses.forEach((row) => {
        data = upsertRow_(data, row);
      });
      return jsonOutput_(saveData_(data));
    }
    const row = parsed;
    let data = loadData_();
    data = upsertRow_(data, row);
    data = saveData_(data);
    return jsonOutput_(data);
  } catch (err) {
    return jsonOutput_({
      ok: false,
      error: String(err),
      updatedAt: new Date().toISOString(),
      responses: [],
    });
  }
}

/**
 * 初回のみ実行: 保存用スプレッドシートを作成し ID を記録する
 */
function setup() {
  const ss = SpreadsheetApp.create("bon-odori-2026-attendance");
  const sheet = ss.getSheets()[0].setName(SHEET_NAME);
  sheet.getRange(DATA_CELL).setValue(
    JSON.stringify({ updatedAt: new Date().toISOString(), responses: [] })
  );
  PropertiesService.getScriptProperties().setProperty("SPREADSHEET_ID", ss.getId());
  Logger.log("SPREADSHEET_ID=" + ss.getId());
  Logger.log("Spreadsheet URL=" + ss.getUrl());
}

/**
 * 既存の attendance.json 相当をまとめて投入（エディタから1回実行）
 * 引数例: seedFromEditor_('[{"name":"坂倉 遥",...}]')
 */
function seedFromEditor_(responsesJson) {
  const list = JSON.parse(responsesJson);
  let data = { updatedAt: new Date().toISOString(), responses: [] };
  if (!Array.isArray(list)) throw new Error("配列を渡してください");
  list.forEach((row) => {
    data = upsertRow_(data, row);
  });
  saveData_(data);
  Logger.log("seeded " + data.responses.length + " rows");
}

/** 本番データのみに戻す（setup 後・テスト削除時） */
function seedCurrentResponses() {
  seedFromEditor_(JSON.stringify(productionResponses_()));
}
