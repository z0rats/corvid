const DEFAULT_BASE_URL = 'http://localhost:4000';

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;

  let selection = '';
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => window.getSelection().toString().trim(),
    });
    selection = result || '';
  } catch (err) {
    // Injection is blocked on chrome:// pages, the Web Store, etc.
    console.warn('Corvid: could not read selection on this page', err);
  }

  const { corvidBaseUrl } = await chrome.storage.local.get('corvidBaseUrl');
  const baseUrl = (corvidBaseUrl || DEFAULT_BASE_URL).replace(/\/$/, '');

  const url = selection
    ? `${baseUrl}/ioc-tools/lookup?q=${encodeURIComponent(selection)}`
    : `${baseUrl}/ioc-tools/lookup`;

  chrome.tabs.create({ url });
});
