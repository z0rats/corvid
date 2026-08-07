importScripts('exif-parser.js', 'ioc-type-detection.js');

const DEFAULT_BASE_URL = 'http://localhost:4000';

// Toolbar icon click opens the side panel (sidepanel.html's Home tab: search, quick links,
// settings) in-place on the current tab, instead of chrome.action.onClicked opening a new tab
// on the backend. These two are mutually exclusive in Chrome — once this is set, onClicked
// simply never fires, so there's no listener for it below.
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch((err) => {
  console.error('Corvid: failed to enable side panel on action click', err);
});

// Kept in sync by hand with frontend/src/features/image-tools/constants/imageConstants.js's
// REVERSE_SEARCH_ENGINES (url-search entries only) — the extension has no build step to share
// code with frontend/ across packages. TinEye is excluded from the "all" bundle (its own menu
// item still opens it) since it's a poor fit for the common case the bundle targets.
const REVERSE_SEARCH_ENGINES = [
  {
    id: 'google',
    name: 'Google Lens',
    inAll: true,
    urlSearch: (url) => `https://lens.google.com/uploadbyurl?url=${encodeURIComponent(url)}`,
  },
  {
    id: 'yandex',
    name: 'Yandex Images',
    inAll: true,
    urlSearch: (url) => `https://yandex.com/images/search?rpt=imageview&url=${encodeURIComponent(url)}`,
  },
  {
    id: 'bing',
    name: 'Bing Visual Search',
    inAll: true,
    urlSearch: (url) => `https://www.bing.com/images/search?q=imgurl:${encodeURIComponent(url)}&view=detailv2&iss=sbi`,
  },
  {
    id: 'tineye',
    name: 'TinEye',
    inAll: false,
    urlSearch: (url) => `https://tineye.com/search?url=${encodeURIComponent(url)}`,
  },
];

// One flat menu ("Corvid") for everything, split by context — image-only items (reverse
// search, EXIF) only ever show on an <img>, the IOC lookup item only on a text selection.
// Not nested submenus-within-submenus: every item below is a direct child of MENU_ROOT_ID.
const MENU_ROOT_ID = 'corvid-menu';
const REVERSE_SEARCH_ALL_ID = 'corvid-reverse-search-all';
const engineMenuId = (id) => `corvid-reverse-search-${id}`;
const EXIF_MENU_ID = 'corvid-image-exif';
const IOC_MENU_ID = 'corvid-ioc-lookup';

// Requested at runtime (not at install) the first time "Show EXIF metadata" is used — the
// image can be hosted on any domain, so reading its bytes needs a host permission covering
// that domain. User chose one broad one-time grant over a per-domain prompt each time.
const EXIF_HOST_PERMISSIONS = { origins: ['http://*/*', 'https://*/*'] };

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({ id: MENU_ROOT_ID, title: 'Corvid', contexts: ['image', 'selection'] });

    chrome.contextMenus.create({
      id: REVERSE_SEARCH_ALL_ID,
      parentId: MENU_ROOT_ID,
      title: 'Reverse search: All (Google, Yandex, Bing)',
      contexts: ['image'],
    });
    for (const engine of REVERSE_SEARCH_ENGINES) {
      chrome.contextMenus.create({
        id: engineMenuId(engine.id),
        parentId: MENU_ROOT_ID,
        title: `Reverse search: ${engine.name}`,
        contexts: ['image'],
      });
    }
    chrome.contextMenus.create({
      type: 'separator',
      id: 'corvid-image-sep',
      parentId: MENU_ROOT_ID,
      contexts: ['image'],
    });
    chrome.contextMenus.create({
      id: EXIF_MENU_ID,
      parentId: MENU_ROOT_ID,
      title: 'Show EXIF metadata',
      contexts: ['image'],
    });

    chrome.contextMenus.create({
      id: IOC_MENU_ID,
      parentId: MENU_ROOT_ID,
      title: 'Search in Corvid',
      contexts: ['selection'],
    });
  });
});

function truncate(value, max) {
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}

// Updates the IOC menu item's label with the detected type right before the menu paints, e.g.
// "Search IPv4 in Corvid: 1.2.3.4" — this is what replaces the old "click toolbar icon with
// text selected" flow. Guarded: onShown is a newer API, and a missing/undefined listener target
// would otherwise throw at load time and take the whole background script down with it.
if (chrome.contextMenus.onShown) {
  chrome.contextMenus.onShown.addListener((info) => {
    const raw = (info.selectionText || '').trim();
    if (!raw) return;

    const type = detectIocType(raw);
    const display = truncate(raw, 50).replace(/&/g, '&&'); // & is a mnemonic marker in menu titles
    const title = type ? `Search ${type} in Corvid: ${display}` : `Search in Corvid: ${display}`;
    chrome.contextMenus.update(IOC_MENU_ID, { title });
    chrome.contextMenus.refresh();
  });
}

function handleReverseSearchClick(info) {
  // data:/blob: image sources aren't fetchable by these engines' servers, only http(s) is.
  if (!info.srcUrl || !/^https?:\/\//i.test(info.srcUrl)) {
    console.warn('Corvid: image has no public URL to reverse-search', info.srcUrl);
    return;
  }
  if (info.menuItemId === REVERSE_SEARCH_ALL_ID) {
    for (const engine of REVERSE_SEARCH_ENGINES.filter((e) => e.inAll)) {
      chrome.tabs.create({ url: engine.urlSearch(info.srcUrl) });
    }
    return;
  }
  const engine = REVERSE_SEARCH_ENGINES.find((e) => engineMenuId(e.id) === info.menuItemId);
  if (engine) chrome.tabs.create({ url: engine.urlSearch(info.srcUrl) });
}

async function openIocLookup(value) {
  const { corvidBaseUrl } = await chrome.storage.local.get('corvidBaseUrl');
  const baseUrl = (corvidBaseUrl || DEFAULT_BASE_URL).replace(/\/$/, '');
  const url = value ? `${baseUrl}/ioc-tools/lookup?q=${encodeURIComponent(value)}` : `${baseUrl}/ioc-tools/lookup`;
  chrome.tabs.create({ url });
}

async function handleIocLookupClick(info) {
  const value = (info.selectionText || '').trim();
  if (!value) return;
  await openIocLookup(value);
}

async function setExifState(tabId, state) {
  await chrome.storage.session.set({ [`exif:${tabId}`]: { ...state, updatedAt: Date.now() } });
}

async function openExifPanel(tabId) {
  // Must run as close to the click's user gesture as possible — no awaited calls before this,
  // and no chrome.sidePanel.setOptions() first (the manifest's side_panel.default_path already
  // points at sidepanel.html, so there's nothing to set). A rejection here previously failed
  // silently since nothing was catching or logging it.
  try {
    await chrome.sidePanel.open({ tabId });
  } catch (err) {
    console.error('Corvid: failed to open EXIF side panel', err);
  }
}

async function fetchAndParseExif(tabId, srcUrl) {
  try {
    const response = await fetch(srcUrl);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const buffer = await response.arrayBuffer();
    const result = parseImageExif(buffer);
    await setExifState(tabId, { status: 'done', srcUrl, result });
  } catch (err) {
    console.error('Corvid: EXIF fetch/parse failed', err);
    await setExifState(tabId, { status: 'error', srcUrl, message: String(err?.message || err) });
  }
}

async function handleExifClick(info, tab) {
  await openExifPanel(tab.id);

  if (!info.srcUrl || !/^https?:\/\//i.test(info.srcUrl)) {
    await setExifState(tab.id, { status: 'error', message: 'This image has no public URL (data:/blob: source) — nothing to fetch.' });
    return;
  }

  await setExifState(tab.id, { status: 'loading', srcUrl: info.srcUrl });

  let hasPermission = await chrome.permissions.contains(EXIF_HOST_PERMISSIONS);
  if (!hasPermission) {
    hasPermission = await chrome.permissions.request(EXIF_HOST_PERMISSIONS).catch((err) => {
      console.error('Corvid: EXIF host permission request failed', err);
      return false;
    });
  }
  if (!hasPermission) {
    await setExifState(tab.id, { status: 'permission-denied', srcUrl: info.srcUrl });
    return;
  }

  await fetchAndParseExif(tab.id, info.srcUrl);
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  try {
    if (info.menuItemId === REVERSE_SEARCH_ALL_ID || String(info.menuItemId).startsWith(engineMenuId(''))) {
      handleReverseSearchClick(info);
      return;
    }
    if (info.menuItemId === EXIF_MENU_ID) {
      if (!tab?.id) return;
      await handleExifClick(info, tab);
      return;
    }
    if (info.menuItemId === IOC_MENU_ID) {
      await handleIocLookupClick(info);
    }
  } catch (err) {
    console.error('Corvid: context menu action failed', err);
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  // Fallback retry path: sidepanel.js's "Grant access" button re-requests the permission itself
  // (a fresh user gesture from within the panel), then asks us to redo the fetch — kept here
  // rather than duplicated in the panel so there's one fetch/parse code path.
  if (message?.type === 'corvid-exif-retry' && message.tabId) {
    fetchAndParseExif(message.tabId, message.srcUrl).then(() => sendResponse({ ok: true }));
    return true;
  }
  // content.js's floating selection popup (content scripts can't call chrome.tabs directly).
  if (message?.type === 'corvid-ioc-open') {
    openIocLookup((message.value || '').trim());
    return undefined;
  }
  return undefined;
});
