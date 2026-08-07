// DeepL-style floating popup icon on text selection — but only ever appears when the selection
// unambiguously matches one of Corvid's supported IOC types (detectIocType from
// ioc-type-detection.js, loaded before this file in manifest.json's content_scripts). Runs on
// every page (see manifest's broad `matches`), so it stays deliberately minimal: no build step,
// isolated in a shadow DOM so it can't be styled-over by the host page and can't leak styles
// into it, and does nothing at all until a qualifying selection is made.
(() => {
  const HOST_ID = 'corvid-selection-popup-host';
  let host = null;
  let button = null;
  let pendingValue = null;
  let debounceTimer = null;

  function ensureHost() {
    if (host) return;
    host = document.createElement('div');
    host.id = HOST_ID;
    Object.assign(host.style, {
      position: 'absolute',
      zIndex: '2147483647',
      display: 'none',
      top: '0',
      left: '0',
    });
    document.documentElement.appendChild(host);

    const shadow = host.attachShadow({ mode: 'open' });
    const style = document.createElement('style');
    style.textContent = `
      button {
        all: initial;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #16171d;
        color: #fff;
        font-size: 14px;
        line-height: 1;
        cursor: pointer;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.35);
        font-family: system-ui, sans-serif;
      }
      button:hover {
        background: #33354a;
      }
    `;
    button = document.createElement('button');
    button.type = 'button';
    button.textContent = '🔎';
    button.title = 'Search in Corvid';
    // Prevent the button's own mousedown from collapsing the text selection before click fires.
    button.addEventListener('mousedown', (event) => event.preventDefault());
    button.addEventListener('click', (event) => {
      event.stopPropagation();
      if (pendingValue) {
        chrome.runtime.sendMessage({ type: 'corvid-ioc-open', value: pendingValue });
      }
      hidePopup();
    });

    shadow.append(style, button);
  }

  function showPopup(rect, value) {
    ensureHost();
    pendingValue = value;
    const top = Math.max(window.scrollY + 4, rect.top + window.scrollY - 34);
    const left = rect.right + window.scrollX - 28;
    host.style.top = `${top}px`;
    host.style.left = `${left}px`;
    host.style.display = 'block';
  }

  function hidePopup() {
    pendingValue = null;
    if (host) host.style.display = 'none';
  }

  function onSelectionChange() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(evaluateSelection, 200);
  }

  function evaluateSelection() {
    const selection = window.getSelection();
    const text = selection && !selection.isCollapsed ? selection.toString().trim() : '';
    if (!text) {
      hidePopup();
      return;
    }

    // Only ever appears on an unambiguous match — no generic "search anything" popup.
    const type = detectIocType(text);
    if (!type) {
      hidePopup();
      return;
    }

    let rect;
    try {
      rect = selection.getRangeAt(0).getBoundingClientRect();
    } catch {
      hidePopup();
      return;
    }
    if (!rect || (rect.width === 0 && rect.height === 0)) {
      hidePopup();
      return;
    }

    showPopup(rect, text);
  }

  document.addEventListener('selectionchange', onSelectionChange);
  document.addEventListener('mousedown', (event) => {
    if (host && !host.contains(event.target)) hidePopup();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') hidePopup();
  });
  window.addEventListener('scroll', hidePopup, true);
})();
