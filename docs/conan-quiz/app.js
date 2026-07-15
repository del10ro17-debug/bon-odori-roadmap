const data = window.CONAN_QUIZ || { levels: {}, questions: [], ranks: [] };

const state = {
  level: null,
  queue: [],
  index: 0,
  correct: 0,
  locked: false,
  choices: [],
  answer: 0,
};

const els = {
  home: document.getElementById("screen-home"),
  quiz: document.getElementById("screen-quiz"),
  result: document.getElementById("screen-result"),
  levelGrid: document.getElementById("levelGrid"),
  progressLabel: document.getElementById("progressLabel"),
  scoreLabel: document.getElementById("scoreLabel"),
  progressBar: document.getElementById("progressBar"),
  quizCard: document.getElementById("quizCard"),
  qLabel: document.getElementById("qLabel"),
  questionText: document.getElementById("questionText"),
  choices: document.getElementById("choices"),
  feedback: document.getElementById("feedback"),
  feedbackResult: document.getElementById("feedbackResult"),
  feedbackExplain: document.getElementById("feedbackExplain"),
  nextBtn: document.getElementById("nextBtn"),
  scoreRing: document.getElementById("scoreRing"),
  scorePercent: document.getElementById("scorePercent"),
  scoreDetail: document.getElementById("scoreDetail"),
  rankTitle: document.getElementById("rankTitle"),
  rankMessage: document.getElementById("rankMessage"),
  retryBtn: document.getElementById("retryBtn"),
  homeBtn: document.getElementById("homeBtn"),
  confetti: document.getElementById("confetti"),
  homeTitle: document.getElementById("homeTitle"),
  homeSubtitle: document.getElementById("homeSubtitle"),
  homeDisclaimer: document.getElementById("homeDisclaimer"),
};

init();

function init() {
  if (data.title) els.homeTitle.textContent = data.title;
  if (data.subtitle) els.homeSubtitle.textContent = data.subtitle;
  if (data.disclaimer) els.homeDisclaimer.textContent = data.disclaimer;

  clearChildren(els.levelGrid);
  Object.values(data.levels).forEach((level) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "level-btn";

    const emoji = document.createElement("span");
    emoji.className = "emoji";
    emoji.setAttribute("aria-hidden", "true");
    emoji.textContent = level.emoji;

    const textWrap = document.createElement("span");
    const strong = document.createElement("strong");
    strong.textContent = level.label;
    const desc = document.createElement("span");
    const stock =
      level.pool === "all"
        ? data.questions.length
        : data.questions.filter((q) => q.level === level.id).length;
    desc.textContent = `${level.description} / 毎回${level.count}問（ストック${stock}）`;
    textWrap.appendChild(strong);
    textWrap.appendChild(desc);

    const arrow = document.createElement("span");
    arrow.className = "arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "›";

    btn.appendChild(emoji);
    btn.appendChild(textWrap);
    btn.appendChild(arrow);
    btn.addEventListener("click", () => startGame(level.id));
    els.levelGrid.appendChild(btn);
  });

  els.nextBtn.addEventListener("click", onNext);
  els.retryBtn.addEventListener("click", () => {
    if (state.level) startGame(state.level);
  });
  els.homeBtn.addEventListener("click", () => showScreen("home"));
}

function startGame(levelId) {
  const level = data.levels[levelId];
  if (!level) return;

  const pool =
    level.pool === "all"
      ? data.questions
      : data.questions.filter((q) => q.level === levelId);
  const count = level.count || 10;
  const queue = shuffle(pool).slice(0, Math.min(count, pool.length));
  if (!queue.length) return;

  state.level = levelId;
  state.queue = queue;
  state.index = 0;
  state.correct = 0;
  state.locked = false;

  showScreen("quiz");
  renderQuestion();
  beep(520, 0.05);
}

function renderQuestion() {
  const item = state.queue[state.index];
  const total = state.queue.length;
  const no = state.index + 1;
  const shuffled = shuffle(
    item.choices.map((text, originalIndex) => ({ text, originalIndex }))
  );
  state.choices = shuffled;
  state.answer = shuffled.findIndex((c) => c.originalIndex === item.answer);

  state.locked = false;
  els.feedback.classList.remove("show");
  els.progressLabel.textContent = `${no} / ${total}`;
  els.scoreLabel.textContent = `正解 ${state.correct}`;
  els.progressBar.style.width = `${((no - 1) / total) * 100}%`;
  els.qLabel.textContent = `QUESTION ${String(no).padStart(2, "0")}`;
  els.questionText.textContent = item.q;

  els.quizCard.style.animation = "none";
  void els.quizCard.offsetWidth;
  els.quizCard.style.animation = "";

  clearChildren(els.choices);
  shuffled.forEach((choice, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "choice";
    btn.textContent = `${"ABCD"[i]}. ${choice.text}`;
    btn.addEventListener("click", () => answer(i));
    els.choices.appendChild(btn);
  });
}

function answer(choiceIndex) {
  if (state.locked) return;
  state.locked = true;

  const item = state.queue[state.index];
  const buttons = [...els.choices.querySelectorAll(".choice")];
  const ok = choiceIndex === state.answer;

  buttons.forEach((btn, i) => {
    btn.disabled = true;
    if (i === state.answer) btn.classList.add("correct");
    else if (i === choiceIndex) btn.classList.add("wrong");
    else btn.classList.add("dim");
  });

  if (ok) {
    state.correct += 1;
    els.feedbackResult.textContent = "せいかい！";
    els.feedbackResult.className = "result ok";
    beep(880, 0.08);
    setTimeout(() => beep(1175, 0.1), 90);
  } else {
    els.feedbackResult.textContent = "ざんねん…";
    els.feedbackResult.className = "result ng";
    beep(220, 0.14);
  }

  els.feedbackExplain.textContent = item.explain || "";
  els.scoreLabel.textContent = `正解 ${state.correct}`;
  els.progressBar.style.width = `${((state.index + 1) / state.queue.length) * 100}%`;
  els.nextBtn.textContent = state.index + 1 >= state.queue.length ? "結果を見る" : "つぎへ";
  els.feedback.classList.add("show");
}

function onNext() {
  if (state.index + 1 >= state.queue.length) {
    showResult();
    return;
  }
  state.index += 1;
  renderQuestion();
}

function showResult() {
  const total = state.queue.length;
  const percent = total ? Math.round((state.correct / total) * 100) : 0;
  const rank = pickRank(percent);

  els.scorePercent.textContent = `${percent}%`;
  els.scoreDetail.textContent = `${state.correct} / ${total}`;
  els.scoreRing.style.setProperty("--score-deg", `${percent * 3.6}deg`);
  els.rankTitle.textContent = rank.title;
  els.rankMessage.textContent = rank.message;

  showScreen("result");
  if (percent >= 70) burstConfetti();
  beep(660, 0.08);
  setTimeout(() => beep(880, 0.1), 100);
  setTimeout(() => beep(1175, 0.12), 200);
}

function pickRank(percent) {
  const ranks = [...(data.ranks || [])].sort((a, b) => a.min - b.min);
  let current = ranks[0] || { title: "探偵見習い", message: "もういちど挑戦だ！" };
  ranks.forEach((r) => {
    if (percent >= r.min) current = r;
  });
  return current;
}

function showScreen(name) {
  els.home.classList.toggle("active", name === "home");
  els.quiz.classList.toggle("active", name === "quiz");
  els.result.classList.toggle("active", name === "result");
}

function shuffle(list) {
  const arr = [...list];
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function clearChildren(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function beep(freq, duration) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    gain.gain.value = 0.04;
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);
    osc.stop(ctx.currentTime + duration + 0.02);
    setTimeout(() => ctx.close(), (duration + 0.05) * 1000);
  } catch (_) {
    // ignore audio failures
  }
}

function burstConfetti() {
  const root = els.confetti;
  root.hidden = false;
  clearChildren(root);
  const colors = ["#d4a017", "#c62828", "#1b7f4a", "#143556", "#f3e2a8"];
  for (let i = 0; i < 36; i += 1) {
    const bit = document.createElement("i");
    bit.style.left = `${Math.random() * 100}%`;
    bit.style.background = colors[i % colors.length];
    bit.style.animationDuration = `${1.4 + Math.random() * 1.2}s`;
    bit.style.animationDelay = `${Math.random() * 0.2}s`;
    root.appendChild(bit);
  }
  setTimeout(() => {
    root.hidden = true;
    clearChildren(root);
  }, 2800);
}
