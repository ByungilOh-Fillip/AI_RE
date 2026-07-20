import "./style.css";

import { fetchHealth } from "./api/client";
import { apiBaseUrl } from "./config";

type ConnectionState = "checking" | "connected" | "disconnected";

function requireElement<T extends Element>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (element === null) {
    throw new Error(`Required element was not found: ${selector}`);
  }
  return element;
}

const app = requireElement<HTMLElement>("#app");

app.innerHTML = `
  <div class="companion-app">
    <header class="app-header">
      <div class="companion-avatar" aria-hidden="true">
        <span>AI</span>
        <span id="status-dot" class="status-dot" data-state="checking"></span>
      </div>
      <div class="header-copy">
        <p class="companion-label">나의 동료</p>
        <h1>AIRE</h1>
        <p id="connection-status" class="connection-status" aria-live="polite">연결 확인 중</p>
      </div>
      <button id="refresh-connection" class="icon-button" type="button" aria-label="연결 상태 다시 확인">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 12a8 8 0 1 1-2.34-5.66M20 4v6h-6"/></svg>
      </button>
    </header>

    <nav class="app-tabs" aria-label="동료 메뉴">
      <button class="tab-button active" type="button" data-view="chat" aria-selected="true">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z"/></svg>
        대화
      </button>
      <button class="tab-button" type="button" data-view="memory" aria-selected="false">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21a9 9 0 1 0-9-9v7l2.5-2.5M8 12h8M12 8v8"/></svg>
        기억
      </button>
    </nav>

    <main id="chat-view" class="app-view active" data-view-panel="chat">
      <section id="chat-messages" class="chat-messages" aria-label="대화 내용" aria-live="polite">
        <div class="date-divider"><span>오늘</span></div>
        <article class="message companion-message">
          <div class="message-bubble">
            <p>여기서 나눈 이야기는 다음 모험에서도 이어져. 오늘은 어떤 하루였어?</p>
          </div>
          <time>방금</time>
        </article>
      </section>

      <section class="composer-area">
        <p class="time-context">
          <span aria-hidden="true">◷</span>
          현실 시간 기준으로 대화해요
        </p>
        <div class="suggestion-list" aria-label="추천 대화">
          <button type="button" class="suggestion-chip">오늘 있었던 일 이야기하기</button>
          <button type="button" class="suggestion-chip">다음 모험 얘기하기</button>
        </div>
        <form id="chat-form" class="chat-composer">
          <label class="sr-only" for="chat-input">AIRE에게 메시지 보내기</label>
          <textarea id="chat-input" rows="1" maxlength="1000" placeholder="AIRE에게 이야기하기"></textarea>
          <button id="send-button" class="send-button" type="submit" aria-label="메시지 보내기">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
          </button>
        </form>
        <p id="composer-notice" class="composer-notice" hidden></p>
      </section>
    </main>

    <main id="memory-view" class="app-view" data-view-panel="memory" hidden>
      <section class="memory-intro">
        <span class="memory-mark" aria-hidden="true">✦</span>
        <p class="section-kicker">함께 쌓은 기억</p>
        <h2>AIRE가 기억하고 있는 이야기</h2>
        <p>직접 들려준 이야기만 저장 후보가 되며, 언제든 확인하고 지울 수 있어요.</p>
      </section>
      <section class="empty-card">
        <div class="empty-icon" aria-hidden="true">✧</div>
        <h3>아직 저장된 기억이 없어요</h3>
        <p>대화를 이어가면 소중한 이야기가 이곳에 나타나요.</p>
        <span class="development-badge">Memory API 연결 예정</span>
      </section>
    </main>
  </div>
`;

const connectionStatus = requireElement<HTMLElement>("#connection-status");
const statusDot = requireElement<HTMLElement>("#status-dot");
const refreshButton = requireElement<HTMLButtonElement>("#refresh-connection");
const chatMessages = requireElement<HTMLElement>("#chat-messages");
const chatForm = requireElement<HTMLFormElement>("#chat-form");
const chatInput = requireElement<HTMLTextAreaElement>("#chat-input");
const composerNotice = requireElement<HTMLElement>("#composer-notice");

function setConnectionState(state: ConnectionState, label: string): void {
  statusDot.dataset.state = state;
  connectionStatus.dataset.state = state;
  connectionStatus.textContent = label;
}

async function checkConnection(): Promise<void> {
  refreshButton.disabled = true;
  setConnectionState("checking", "연결 확인 중");

  try {
    const health = await fetchHealth(apiBaseUrl);
    setConnectionState("connected", `C PC 연결됨 · ${health.ai_mode}`);
  } catch {
    setConnectionState("disconnected", "C PC에 연결할 수 없음");
  } finally {
    refreshButton.disabled = false;
  }
}

function formatCurrentTime(): string {
  return new Intl.DateTimeFormat("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());
}

function appendUserMessage(text: string): void {
  const message = document.createElement("article");
  message.className = "message user-message";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  const content = document.createElement("p");
  content.textContent = text;
  bubble.append(content);

  const time = document.createElement("time");
  time.textContent = formatCurrentTime();
  message.append(bubble, time);
  chatMessages.append(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showComposerNotice(message: string): void {
  composerNotice.textContent = message;
  composerNotice.hidden = false;
}

document.querySelectorAll<HTMLButtonElement>(".tab-button").forEach((button) => {
  button.addEventListener("click", () => {
    const target = button.dataset.view;
    if (target === undefined) {
      return;
    }

    document.querySelectorAll<HTMLButtonElement>(".tab-button").forEach((tab) => {
      const active = tab === button;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-selected", String(active));
    });

    document.querySelectorAll<HTMLElement>("[data-view-panel]").forEach((panel) => {
      const active = panel.dataset.viewPanel === target;
      panel.classList.toggle("active", active);
      panel.hidden = !active;
    });
  });
});

document.querySelectorAll<HTMLButtonElement>(".suggestion-chip").forEach((button) => {
  button.addEventListener("click", () => {
    chatInput.value = button.textContent?.trim() ?? "";
    chatInput.focus();
  });
});

chatInput.addEventListener("input", () => {
  chatInput.style.height = "auto";
  chatInput.style.height = `${Math.min(chatInput.scrollHeight, 120)}px`;
  composerNotice.hidden = true;
});

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (message.length === 0) {
    return;
  }

  appendUserMessage(message);
  chatInput.value = "";
  chatInput.style.height = "auto";
  showComposerNotice("대화 API가 연결되면 AIRE의 답변이 여기에 표시돼요.");
});

refreshButton.addEventListener("click", () => {
  void checkConnection();
});

void checkConnection();
