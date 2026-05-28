const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function normalizeRow(row) {
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

function upsertRow(data, row) {
  const normalized = normalizeRow(row);
  if (!normalized) return data;
  const list = Array.isArray(data.responses) ? data.responses : [];
  const idx = list.findIndex((r) => r && r.name === normalized.name);
  if (idx >= 0) {
    const prevAt = Date.parse(list[idx].updatedAt || "") || 0;
    const nextAt = Date.parse(normalized.updatedAt || "") || 0;
    if (nextAt >= prevAt) list[idx] = normalized;
  } else {
    list.push(normalized);
  }
  data.responses = list.sort((a, b) =>
    String(a.name).localeCompare(String(b.name), "ja")
  );
  data.updatedAt = new Date().toISOString();
  return data;
}

async function loadData(env) {
  const raw = await env.ATTENDANCE.get("data");
  if (!raw) return { updatedAt: new Date().toISOString(), responses: [] };
  try {
    return JSON.parse(raw);
  } catch {
    return { updatedAt: new Date().toISOString(), responses: [] };
  }
}

async function saveData(env, data) {
  data.updatedAt = new Date().toISOString();
  await env.ATTENDANCE.put("data", JSON.stringify(data));
  return data;
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    if (request.method === "GET") {
      return jsonResponse(await loadData(env));
    }

    if (request.method === "POST") {
      try {
        const body = await request.json();
        if (env.SYNC_KEY && body.syncKey !== env.SYNC_KEY) {
          return jsonResponse({ ok: false, error: "unauthorized" }, 401);
        }
        let data = await loadData(env);
        data = upsertRow(data, body.row || body);
        data = await saveData(env, data);
        return jsonResponse(data);
      } catch (err) {
        return jsonResponse({ ok: false, error: String(err) }, 500);
      }
    }

    return jsonResponse({ error: "Method not allowed" }, 405);
  },
};
