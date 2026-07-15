function extractPageText() {
  const selectors = [
    "main",
    "[role='main']",
    "article",
    ".terms",
    ".privacy-policy",
    "#terms",
    "#privacy",
    ".content",
    "#content",
  ];

  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element?.innerText?.trim().length > 200) {
      return element.innerText.trim();
    }
  }

  return document.body.innerText.trim();
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === "extractText") {
    sendResponse({ ok: true, text: extractPageText() });
  }
  return true;
});
