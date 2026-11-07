/**
 * Чат-виджет ИИ-ассистента аналитического портала.
 * Подключение на любую страницу одной строкой:
 *   <script src="/widget/assistant.js" data-api="/api" defer></script>
 * (+ <link rel="stylesheet" href="/widget/assistant.css">)
 *
 * После ответа с распознанным дэшбордом виджет диспатчит событие
 * window "ai-assistant:open-dashboard" { detail: { viewUrl, id } } —
 * портал подписывается и переключает рабочую область (в целевой версии —
 * навигация по URL-вью через Tableau Embedding API v3).
 */
(function () {
  "use strict";

  var scriptEl = document.currentScript || document.querySelector('script[data-ai-assistant]');
  var API_BASE = (scriptEl && scriptEl.getAttribute("data-api")) || "/api";

  var STARTER_CHIPS = [
    { label: "Выручка с начала года", query: "покажи выручку с начала года" },
    { label: "EBITDA и маржинальность", query: "какая EBITDA" },
    { label: "Продажи по регионам", query: "продажи по регионам" },
    { label: "Текучесть кадров", query: "какая текучесть персонала" }
  ];

  var state = {
    open: false,
    busy: false,
    sessionId: null,
    history: []
  };

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  // --- DOM ---
  var root = el("div");
  root.id = "aiw-root";

  var fab = el("button", "aiw-fab", "◔");
  fab.setAttribute("aria-label", "Открыть ассистента");
  var dot = el("span", "aiw-dot");
  fab.appendChild(dot);

  var panel = el("div", "aiw-panel");
  panel.style.display = "none";

  var header = el("div", "aiw-header");
  var headerText = el("div");
  headerText.appendChild(el("div", "aiw-title", "Ассистент портала"));
  headerText.appendChild(el("div", "aiw-sub", "Спросите о показателях — открою нужный дэшборд"));
  var closeBtn = el("button", "aiw-close", "×");
  closeBtn.setAttribute("aria-label", "Свернуть ассистента");
  header.appendChild(headerText);
  header.appendChild(closeBtn);

  var messages = el("div", "aiw-messages");
  var chipsRow = el("div", "aiw-chips");

  var inputRow = el("div", "aiw-input-row");
  var input = el("input", "aiw-input");
  input.type = "text";
  input.placeholder = "Например: покажи выручку с начала года";
  input.setAttribute("aria-label", "Сообщение ассистенту");
  var sendBtn = el("button", "aiw-send", "Отправить");
  inputRow.appendChild(input);
  inputRow.appendChild(sendBtn);

  panel.appendChild(header);
  panel.appendChild(messages);
  panel.appendChild(chipsRow);
  panel.appendChild(inputRow);

  root.appendChild(panel);
  root.appendChild(fab);
  document.body.appendChild(root);

  // --- Рендер ---
  function scrollDown() {
    messages.scrollTop = messages.scrollHeight;
  }

  function addMessage(role, text, dashboard) {
    var msg = el("div", "aiw-msg aiw-msg-" + role, text);
    if (role === "bot" && dashboard) {
      var btn = el("button", "aiw-open-btn", "Открыть дэшборд: " + dashboard.title);
      btn.addEventListener("click", function () {
        openDashboard(dashboard);
      });
      msg.appendChild(document.createElement("br"));
      msg.appendChild(btn);
    }
    messages.appendChild(msg);
    scrollDown();
    return msg;
  }

  function showTyping() {
    var t = el("div", "aiw-typing");
    t.id = "aiw-typing";
    t.appendChild(el("span"));
    t.appendChild(el("span"));
    t.appendChild(el("span"));
    messages.appendChild(t);
    scrollDown();
  }

  function hideTyping() {
    var t = document.getElementById("aiw-typing");
    if (t) t.remove();
  }

  function renderChips(chips) {
    chipsRow.innerHTML = "";
    chips.forEach(function (c) {
      var b = el("button", "aiw-chip", c.label);
      b.addEventListener("click", function () {
        send(c.query);
      });
      chipsRow.appendChild(b);
    });
    chipsRow.style.display = chips.length ? "flex" : "none";
  }

  function openDashboard(dashboard) {
    // Целевая точка интеграции с рабочей областью портала / Tableau Embedding API v3.
    window.dispatchEvent(
      new CustomEvent("ai-assistant:open-dashboard", {
        detail: { id: dashboard.id, viewUrl: dashboard.view_url, title: dashboard.title }
      })
    );
  }

  // --- Сеть ---
  function send(text) {
    text = (text || "").trim();
    if (!text || state.busy) return;

    state.busy = true;
    sendBtn.disabled = true;
    input.value = "";
    renderChips([]);
    addMessage("user", text);
    state.history.push({ role: "user", text: text });
    showTyping();

    fetch(API_BASE + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, message: text })
    })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        hideTyping();
        state.sessionId = data.session_id;
        addMessage("bot", data.reply, data.dashboard || null);
        state.history.push({ role: "bot", text: data.reply });
        if (data.chips && data.chips.length) renderChips(data.chips);
        if (data.dashboard) openDashboard(data.dashboard);
      })
      .catch(function () {
        hideTyping();
        addMessage("bot", "Сервис ассистента временно недоступен. Попробуйте ещё раз чуть позже.");
      })
      .finally(function () {
        state.busy = false;
        sendBtn.disabled = false;
        input.focus();
      });
  }

  // --- События ---
  function toggle(open) {
    state.open = open;
    panel.style.display = open ? "flex" : "none";
    fab.style.display = open ? "none" : "flex";
    if (open) {
      if (!state.history.length) {
        addMessage(
          "bot",
          "Здравствуйте! Спросите о показателях компании в свободной форме — " +
            "я дам краткий вывод и открою нужный дэшборд."
        );
        renderChips(STARTER_CHIPS);
      }
      input.focus();
      scrollDown();
    }
  }

  fab.addEventListener("click", function () { toggle(true); });
  closeBtn.addEventListener("click", function () { toggle(false); });
  sendBtn.addEventListener("click", function () { send(input.value); });
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") send(input.value);
  });
})();
