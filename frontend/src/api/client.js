const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function isExtensionContext() {
  return typeof chrome !== "undefined" && chrome.runtime?.id;
}

async function directFetch(path, body) {
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

function extensionMessage(action, payload) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ action, ...payload }, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }
      if (!response?.ok) {
        reject(new Error(response?.error || "Request failed"));
        return;
      }
      resolve(response.data);
    });
  });
}

export async function analyzeAgreement(content, documentType = "agreement") {
  if (isExtensionContext()) {
    return extensionMessage("analyze", { content, documentType });
  }
  return directFetch("/api/analyze", { content, document_type: documentType });
}

export async function askQuestion(agreementId, question) {
  if (isExtensionContext()) {
    return extensionMessage("question", { agreementId, question });
  }
  return directFetch("/api/question", {
    agreement_id: agreementId,
    question,
  });
}

export async function extractPageText() {
  if (!isExtensionContext()) {
    return null;
  }

  return new Promise((resolve, reject) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (!tab?.id) {
        reject(new Error("No active tab found"));
        return;
      }

      chrome.tabs.sendMessage(tab.id, { action: "extractText" }, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error("Could not read page text. Try refreshing the page."));
          return;
        }
        if (!response?.ok) {
          reject(new Error("Failed to extract page text"));
          return;
        }
        resolve(response.text);
      });
    });
  });
}

export { isExtensionContext };
