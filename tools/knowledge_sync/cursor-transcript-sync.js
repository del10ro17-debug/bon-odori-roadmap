#!/usr/bin/env node
/**
 * Cursor agent-transcripts → Obsidian
 *
 * Reads ~/.cursor/projects/{project}/agent-transcripts/{session}/*.jsonl
 * Writes wiki/sources/cursor/{id}.md + .raw/cursor-chat-*.md
 * Updates hot.md cursor: line for the day
 *
 * LaunchAgent: com.user.cursor-daily-sync（毎日 08:30 JST、本スクリプトを内包）
 */

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const HOME = process.env.HOME;
const PROJECTS_DIR = path.join(HOME, ".cursor/projects");
const SYNC_DIR = path.join(HOME, ".claude/cursor-sync");
const STATE_DIR = path.join(SYNC_DIR, "state");
const STATE_FILE = path.join(STATE_DIR, "transcript-sync.json");
const VAULT = path.join(
  HOME,
  "Library/Mobile Documents/iCloud~md~Obsidian/Documents/claude-obsidian"
);
const WIKI_DIR = path.join(VAULT, "wiki");
const RAW_DIR = path.join(VAULT, ".raw");
const SOURCES_DIR = path.join(WIKI_DIR, "sources/cursor");
const HOT_FILE = path.join(WIKI_DIR, "hot.md");
const MAX_ASSISTANT_CHARS = 120000;
const MAX_TURN_CHARS = 8000;
const HOT_CONTEXT_MAX = 20;

function log(msg) {
  console.log(`[${new Date().toISOString()}] ${msg}`);
}

function jstDate(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const v = Object.fromEntries(parts.map((p) => [p.type, p.value]));
  return `${v.year}-${v.month}-${v.day}`;
}

function ensureLocal(filePath) {
  try {
    fs.accessSync(filePath, fs.constants.R_OK);
    return;
  } catch (e) {
    if (e.errno !== -11 && e.code !== "ENOENT") throw e;
  }
  try {
    execFileSync("brctl", ["download", filePath], { stdio: "ignore", timeout: 5000 });
  } catch (_) {}
}

function readFileLocal(filePath) {
  try {
    return fs.readFileSync(filePath, "utf8");
  } catch (e) {
    if (e.errno !== -11) throw e;
    ensureLocal(filePath);
    return fs.readFileSync(filePath, "utf8");
  }
}

function writeFileAtomic(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const tmp = `${filePath}.tmp-${process.pid}`;
  fs.writeFileSync(tmp, content, "utf8");
  fs.renameSync(tmp, filePath);
}

function loadState() {
  try {
    return JSON.parse(readFileLocal(STATE_FILE));
  } catch {
    return { files: {} };
  }
}

function saveState(state) {
  fs.mkdirSync(STATE_DIR, { recursive: true });
  writeFileAtomic(STATE_FILE, `${JSON.stringify(state, null, 2)}\n`);
}

function parseArgs(argv = process.argv) {
  const args = { days: null, force: false };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--force") args.force = true;
    else if (arg === "--days" && argv[i + 1]) {
      args.days = Number(argv[++i]) || null;
    }
  }
  return args;
}

function isWithinDays(stat, days) {
  if (!days) return true;
  const cutoff = Date.now() - days * 24 * 3600 * 1000;
  return stat.mtimeMs >= cutoff;
}

function slugify(text, maxLen = 40) {
  return String(text || "session")
    .replace(/<[^>]+>/g, " ")
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase()
    .slice(0, maxLen) || "session";
}

function projectSlug(projectDirName) {
  const m = projectDirName.match(/^Users-[^-]+-(.+)$/i);
  return m ? m[1].replace(/-/g, "/") : projectDirName;
}

function extractUserQuery(text) {
  const m = text.match(/<user_query>\s*([\s\S]*?)\s*<\/user_query>/i);
  return (m ? m[1] : text)
    .replace(/<timestamp>[\s\S]*?<\/timestamp>/gi, "")
    .replace(/<[^>]+>/g, "")
    .trim();
}

function extractTextParts(content) {
  if (!Array.isArray(content)) return [];
  return content
    .filter((p) => p && p.type === "text" && typeof p.text === "string")
    .map((p) => p.text.trim())
    .filter((t) => t && t !== "[REDACTED]");
}

function truncate(text, max) {
  if (text.length <= max) return text;
  return `${text.slice(0, max - 20)}\n\n…（省略 ${text.length - max + 20} 文字）`;
}

function parseTranscriptLines(lines) {
  const turns = [];
  let current = null;

  for (const line of lines) {
    if (!line.trim()) continue;
    let row;
    try {
      row = JSON.parse(line);
    } catch {
      continue;
    }
    if (row.type === "turn_ended") continue;
    if (row.role !== "user" && row.role !== "assistant") continue;

    const parts = extractTextParts(row.message?.content);
    if (!parts.length) continue;
    const text = parts.join("\n\n").trim();
    if (!text) continue;

    if (row.role === "user") {
      if (current) turns.push(current);
      current = { user: extractUserQuery(text), assistant: "" };
    } else if (current) {
      current.assistant = current.assistant
        ? `${current.assistant}\n\n${text}`
        : text;
    } else {
      current = { user: "(続き)", assistant: text };
    }
  }
  if (current) turns.push(current);
  return turns;
}

function sessionTitle(turns) {
  const first = turns.find((t) => t.user && t.user !== "(続き)");
  if (!first) return "Cursor session";
  return truncate(first.user.replace(/\s+/g, " "), 80);
}

function buildMarkdown({ sessionId, project, date, title, turns, updatedIso }) {
  const fm = [
    "---",
    "type: source",
    `title: "${title.replace(/"/g, '\\"')}"`,
    "tags:",
    "  - source",
    "  - cursor",
    `  - ${project.replace(/\//g, "-")}`,
    "status: current",
    `session_id: ${sessionId}`,
    `project: ${project}`,
    `date: ${date}`,
    `updated: ${updatedIso}`,
    "related:",
    "  - \"[[sources/_index]]\"",
    "  - \"[[company-hq]]\"",
    "---",
    "",
    `# ${title}`,
    "",
    `- **Project**: ${project}`,
    `- **Session**: ${sessionId}`,
    `- **Updated**: ${updatedIso}`,
    "",
  ];

  const body = [];
  for (const [i, turn] of turns.entries()) {
    body.push(`## Turn ${i + 1}`, "");
    body.push("### User", "", turn.user, "");
    if (turn.assistant) {
      body.push("### Assistant", "", truncate(turn.assistant, MAX_TURN_CHARS), "");
    }
  }

  return fm.concat(body).join("\n");
}

function listTranscriptFiles() {
  const out = [];
  if (!fs.existsSync(PROJECTS_DIR)) return out;

  const projectDirs = fs
    .readdirSync(PROJECTS_DIR)
    .sort((a, b) => {
      const score = (d) => (d.includes("company-hq") ? 0 : 1);
      return score(a) - score(b);
    });

  const seenSessionIds = new Set();

  for (const projectDir of projectDirs) {
    const base = path.join(PROJECTS_DIR, projectDir, "agent-transcripts");
    if (!fs.existsSync(base)) continue;
    for (const sessionDir of fs.readdirSync(base)) {
      if (sessionDir === "subagents") continue;
      const dirPath = path.join(base, sessionDir);
      if (!fs.statSync(dirPath).isDirectory()) continue;

      const mainFile = path.join(dirPath, `${sessionDir}.jsonl`);
      if (!fs.existsSync(mainFile)) continue;
      if (seenSessionIds.has(sessionDir)) continue;
      seenSessionIds.add(sessionDir);

      out.push({
        absPath: mainFile,
        sessionId: sessionDir,
        project: projectSlug(projectDir),
      });
    }
  }
  return out;
}

function updateHotCache(summaries) {
  if (!summaries.length || !fs.existsSync(HOT_FILE)) return;
  const today = jstDate();
  const line = `${today} cursor: ${summaries.slice(0, 3).join(" / ")}`.slice(0, 200);
  let content = readFileLocal(HOT_FILE);
  const lines = content.split("\n");
  const start = lines.findIndex((l) => l.trim() === "# Recent Context");
  if (start === -1) return;

  let end = lines.length;
  for (let i = start + 1; i < lines.length; i++) {
    if (lines[i].startsWith("## ")) {
      end = i;
      break;
    }
  }

  const contextLines = [];
  for (let i = start + 1; i < end; i++) {
    const l = lines[i];
    if (!l.trim()) continue;
    if (l.startsWith("Navigation:")) {
      contextLines.push(l);
      continue;
    }
    if (l.startsWith("See [[log]]")) continue;
    if (l.startsWith(`${today} cursor:`)) continue;
    contextLines.push(l);
  }
  contextLines.unshift(line);
  while (contextLines.filter((l) => !l.startsWith("Navigation:")).length > HOT_CONTEXT_MAX) {
    const idx = contextLines.findIndex((l) => !l.startsWith("Navigation:") && !l.startsWith("See "));
    if (idx === -1) break;
    contextLines.splice(idx, 1);
  }

  const rebuilt = [
    ...lines.slice(0, start + 1),
    ...contextLines,
    "",
    "See [[log]] for earlier entries.",
    ...lines.slice(end),
  ];
  content = rebuilt.join("\n");
  content = content.replace(/^updated: .+$/m, `updated: ${today}T${new Date().toISOString().slice(11, 19)}`);
  writeFileAtomic(HOT_FILE, content);
  log(`hot.md 更新: ${line}`);
}

function processFile(entry, state, opts = {}) {
  const stat = fs.statSync(entry.absPath);
  const prev = state.files[entry.absPath] || {};
  const raw = readFileLocal(entry.absPath);
  const lines = raw.split("\n");
  const lineCount = lines.length;

  if (!opts.force && prev.lineCount === lineCount && prev.mtimeMs === stat.mtimeMs) {
    return null;
  }

  const turns = parseTranscriptLines(lines);
  if (!turns.length) {
    state.files[entry.absPath] = { lineCount, mtimeMs: stat.mtimeMs, skipped: true };
    return null;
  }

  const date = jstDate(stat.mtime);
  const title = sessionTitle(turns);
  const updatedIso = new Date().toISOString().slice(0, 19);
  const md = buildMarkdown({
    sessionId: entry.sessionId,
    project: entry.project,
    date,
    title,
    turns,
    updatedIso,
  });

  const wikiRel = `wiki/sources/cursor/${entry.sessionId}.md`;
  const wikiPath = path.join(VAULT, wikiRel);
  writeFileAtomic(wikiPath, md);

  const slug = slugify(title);
  const id8 = entry.sessionId.slice(0, 8);
  const rawName = `cursor-chat-${date}-${slug}-${id8}.md`;
  const rawPath = path.join(RAW_DIR, rawName);
  const rawBody = md.replace(
    /^---\n([\s\S]*?)\n---/,
    [
      "---",
      "source: Cursor Agent Transcript",
      `session_id: ${entry.sessionId}`,
      `project: ${entry.project}`,
      `date: ${date}`,
      `synced_at: ${updatedIso}`,
      "$1",
      "---",
    ].join("\n")
  );
  writeFileAtomic(rawPath, rawBody);

  state.files[entry.absPath] = {
    lineCount,
    mtimeMs: stat.mtimeMs,
    wikiFile: wikiRel,
    rawFile: rawName,
    title,
    updatedAt: updatedIso,
  };

  log(`同期: ${entry.project} / ${title.slice(0, 60)} → ${wikiRel}`);
  return title.replace(/\s+/g, " ").slice(0, 80);
}

function main(options = {}) {
  const cli = parseArgs();
  const days = options.days ?? cli.days;
  const force = options.force ?? cli.force;

  log(`cursor-transcript-sync 開始${days ? ` (直近 ${days} 日)` : ""}${force ? " [force]" : ""}`);
  const state = loadState();
  const files = listTranscriptFiles();
  const summaries = [];
  let scanned = 0;
  let inWindow = 0;

  for (const entry of files) {
    try {
      const stat = fs.statSync(entry.absPath);
      scanned += 1;
      if (!isWithinDays(stat, days)) continue;
      inWindow += 1;
      const summary = processFile(entry, state, { force });
      if (summary) summaries.push(summary);
    } catch (e) {
      log(`スキップ ${entry.absPath}: ${e.message}`);
    }
  }

  saveState(state);

  if (summaries.length) {
    try {
      updateHotCache(summaries);
    } catch (e) {
      log(`hot.md 更新失敗: ${e.message}`);
    }
  }

  log(`完了: ${summaries.length} セッション更新 / ${inWindow} 件対象（走査 ${scanned}）`);
  return summaries.length;
}

if (require.main === module) {
  try {
    main();
  } catch (e) {
    log(`エラー: ${e.message}`);
    process.exit(1);
  }
}

module.exports = { main, parseTranscriptLines, extractUserQuery };
