const API_BASE = "http://127.0.0.1:8000";

async function apiRequest(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return response.json();
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  (async () => {
    try {
      if (message.action === "analyze") {
        const data = await apiRequest("/api/analyze", {
          content: message.content,
          document_type: message.documentType || "agreement",
        });
        sendResponse({ ok: true, data });
        return;
      }

      if (message.action === "question") {
        const data = await apiRequest("/api/question", {
          agreement_id: message.agreementId,
          question: message.question,
        });
        sendResponse({ ok: true, data });
        return;
      }

      if (message.action === "health") {
        const response = await fetch(`${API_BASE}/health`);
        sendResponse({ ok: response.ok, data: await response.json() });
        return;
      }

      sendResponse({ ok: false, error: "Unknown action" });
    } catch (error) {
      sendResponse({ ok: false, error: error.message });
    }
  })();

  return true;
});

chrome.action.onClicked.addListener(async (tab) => {
  if (tab.id) {
    await chrome.sidePanel.open({ tabId: tab.id });
  }
});
