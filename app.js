"use strict";

const $ = (id) => document.getElementById(id);
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const micBtn = $("micBtn");
const statusEl = $("status");
const transcriptEl = $("transcript");
const resultCard = $("resultCard");
const resultMain = $("resultMain");
const resultSub = $("resultSub");

let recognition = null;
let listening = false;
let units = {};

// ---------------------------------------------------------------- helpers
function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function showResult(main, sub, isError = false) {
  resultCard.hidden = false;
  resultCard.classList.toggle("error", isError);
  resultMain.textContent = main;
  resultSub.textContent = sub || "";
}

function speak(text) {
  if (!$("speakToggle").checked || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = $("lang").value;
  window.speechSynthesis.speak(utterance);
}

function formatTime(sqliteUtc) {
  const d = new Date(sqliteUtc.replace(" ", "T") + "Z");
  return isNaN(d) ? sqliteUtc : d.toLocaleString();
}

// ---------------------------------------------------------------- API
async function convert(text) {
  try {
    const res = await fetch("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (!res.ok) {
      const detail = typeof data.detail === "string" ? data.detail : "That input isn't valid.";
      showResult("Couldn't convert that", detail, true);
      speak(detail);
      setStatus("Try again", true);
      return;
    }
    showResult(data.display, `Heard: “${data.query}”`);
    speak(data.spoken);
    setStatus("Ready");
    loadHistory();
  } catch (err) {
    showResult("Server unreachable", "Check that the app is running and try again.", true);
    setStatus("Network error", true);
  }
}

async function loadHistory() {
  try {
    const items = await (await fetch("/api/history")).json();
    const list = $("history");
    list.replaceChildren();
    $("historyEmpty").hidden = items.length > 0;
    for (const item of items) {
      const li = document.createElement("li");
      li.title = "Click to run again";
      const main = document.createElement("div");
      main.className = "h-main";
      main.textContent = item.display;
      const sub = document.createElement("div");
      sub.className = "h-sub";
      sub.textContent = `“${item.query}” · ${formatTime(item.created_at)}`;
      li.append(main, sub);
      li.addEventListener("click", () => convert(item.query));
      list.appendChild(li);
    }
  } catch { /* history is non-critical */ }
}

// ---------------------------------------------------------------- voice
function setupRecognition() {
  if (!SpeechRecognition) {
    micBtn.disabled = true;
    setStatus("Voice input isn't supported in this browser. Use Chrome or Edge, or type below.", true);
    return;
  }
  recognition = new SpeechRecognition();
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;
  recognition.continuous = false;

  recognition.onstart = () => {
    listening = true;
    micBtn.textContent = "Stop listening";
    micBtn.classList.add("listening");
    micBtn.setAttribute("aria-pressed", "true");
    setStatus("Listening…");
    transcriptEl.textContent = "";
  };

  recognition.onresult = (event) => {
    let interim = "", final = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const t = event.results[i][0].transcript;
      if (event.results[i].isFinal) final += t; else interim += t;
    }
    transcriptEl.textContent = final || interim;
    if (final) {
      setStatus("Converting…");
      convert(final.trim());
    }
  };

  recognition.onerror = (event) => {
    const messages = {
      "not-allowed": "Microphone blocked. Allow mic access in your browser's address bar.",
      "service-not-allowed": "Microphone blocked. Allow mic access in your browser's address bar.",
      "no-speech": "I didn't hear anything. Try again.",
      "audio-capture": "No microphone found.",
      "network": "Speech service needs an internet connection.",
    };
    setStatus(messages[event.error] || `Voice error: ${event.error}`, true);
  };

  recognition.onend = () => {
    listening = false;
    micBtn.textContent = "Start listening";
    micBtn.classList.remove("listening");
    micBtn.setAttribute("aria-pressed", "false");
    if (statusEl.textContent === "Listening…") setStatus("Ready");
  };
}

micBtn.addEventListener("click", () => {
  if (!recognition) return;
  if (listening) { recognition.stop(); return; }
  window.speechSynthesis?.cancel();
  recognition.lang = $("lang").value;
  try { recognition.start(); } catch { /* already started */ }
});

// ---------------------------------------------------------------- typed + manual input
$("textForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const text = $("textInput").value.trim();
  if (text) { transcriptEl.textContent = text; convert(text); }
});

document.querySelectorAll(".chip").forEach((chip) =>
  chip.addEventListener("click", () => { transcriptEl.textContent = chip.textContent; convert(chip.textContent); })
);

function fillSelect(select, names) {
  select.replaceChildren(...names.map((n) => new Option(n, n)));
}

function categoryOf(name) {
  return Object.keys(units).find((c) => units[c].includes(name));
}

async function setupManualForm() {
  try {
    units = await (await fetch("/api/units")).json();
  } catch { return; }
  const from = $("manualFrom");
  for (const [category, names] of Object.entries(units)) {
    const group = document.createElement("optgroup");
    group.label = category;
    names.forEach((n) => group.appendChild(new Option(n, n)));
    from.appendChild(group);
  }
  const syncTo = () => {
    const names = units[categoryOf(from.value)];
    fillSelect($("manualTo"), names);
    if (names.length > 1) $("manualTo").selectedIndex = 1;
  };
  from.addEventListener("change", syncTo);
  from.value = "kilometer";
  syncTo();
  $("manualTo").value = "mile";
}

$("manualForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const text = `${$("manualValue").value} ${$("manualFrom").value} to ${$("manualTo").value}`;
  transcriptEl.textContent = text;
  convert(text);
});

$("clearBtn").addEventListener("click", async () => {
  await fetch("/api/history", { method: "DELETE" });
  loadHistory();
});

// ---------------------------------------------------------------- init
setupRecognition();
setupManualForm();
loadHistory();
