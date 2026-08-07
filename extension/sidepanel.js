const DEFAULT_BASE_URL = 'http://localhost:4000';

// Route names ported by hand from frontend/src/core/config/routes.jsx — kept short since this
// is just a handful of common entry points, not a mirror of the app's full nav.
const QUICK_LINKS = [
  { label: 'IOC Lookup', path: 'ioc-tools/lookup' },
  { label: 'Domain Finder', path: 'ioc-tools/domain-finder' },
  { label: 'Username Search', path: 'username-search' },
  { label: 'Image Tools', path: 'image-tools' },
];

let activeTabId = null;
let currentView = 'home';

const tabHomeButton = document.getElementById('tab-home');
const tabExifButton = document.getElementById('tab-exif');
const homeView = document.getElementById('home-view');
const exifView = document.getElementById('exif-view');
const content = document.getElementById('content');

function setView(view) {
  currentView = view;
  homeView.style.display = view === 'home' ? 'block' : 'none';
  exifView.style.display = view === 'exif' ? 'block' : 'none';
  tabHomeButton.classList.toggle('active', view === 'home');
  tabExifButton.classList.toggle('active', view === 'exif');
}

tabHomeButton.addEventListener('click', () => setView('home'));
tabExifButton.addEventListener('click', () => {
  if (!tabExifButton.disabled) setView('exif');
});

// --- Home view: quick search + shortcuts + settings, so the toolbar icon opens something
// useful in-place instead of blindly opening a new tab on the backend. ---

async function getBaseUrl() {
  const { corvidBaseUrl } = await chrome.storage.local.get('corvidBaseUrl');
  return (corvidBaseUrl || DEFAULT_BASE_URL).replace(/\/$/, '');
}

async function initQuickLinks() {
  const baseUrl = await getBaseUrl();
  const container = document.getElementById('quick-links');
  container.innerHTML = '';
  for (const link of QUICK_LINKS) {
    const a = document.createElement('a');
    a.href = `${baseUrl}/${link.path}`;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.textContent = link.label;
    container.appendChild(a);
  }
}

function initSearch() {
  const input = document.getElementById('search-input');
  const hint = document.getElementById('search-hint');
  const button = document.getElementById('search-button');

  input.addEventListener('input', () => {
    const value = input.value.trim();
    const type = value ? detectIocType(value) : null;
    hint.textContent = value ? (type ? `Detected: ${type}` : 'No supported IOC type detected — you can still search it as-is.') : '';
    button.disabled = !value;
  });

  const search = () => {
    const value = input.value.trim();
    if (!value) return;
    chrome.runtime.sendMessage({ type: 'corvid-ioc-open', value });
  };
  button.addEventListener('click', search);
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') search();
  });
}

function initSettings() {
  const input = document.getElementById('base-url');
  const status = document.getElementById('settings-status');

  getBaseUrl().then((baseUrl) => {
    input.value = baseUrl;
  });

  document.getElementById('save-base-url').addEventListener('click', async () => {
    const value = input.value.trim().replace(/\/$/, '') || DEFAULT_BASE_URL;
    await chrome.storage.local.set({ corvidBaseUrl: value });
    input.value = value;
    status.textContent = 'Saved.';
    initQuickLinks();
    setTimeout(() => {
      status.textContent = '';
    }, 1500);
  });
}

// --- EXIF view: unchanged from the right-click "Show EXIF metadata" flow, just now one of two
// tabs instead of the panel's only content. ---

const ORIENTATIONS = {
  1: 'Normal',
  2: 'Flipped horizontally',
  3: 'Rotated 180°',
  4: 'Flipped vertically',
  5: 'Rotated 90° CW + flipped',
  6: 'Rotated 90° CW',
  7: 'Rotated 90° CCW + flipped',
  8: 'Rotated 90° CCW',
};

const EXPOSURE_PROGRAMS = {
  0: 'Not defined',
  1: 'Manual',
  2: 'Normal',
  3: 'Aperture priority',
  4: 'Shutter priority',
  5: 'Creative',
  6: 'Action',
  7: 'Portrait',
  8: 'Landscape',
};

function formatDateTime(raw) {
  if (!raw) return null;
  return raw.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3');
}

function formatExposureTime(value) {
  if (value == null) return null;
  if (value >= 1) return `${value} s`;
  const denominator = Math.round(1 / value);
  return `1/${denominator} s`;
}

function formatRows(rows) {
  const visible = rows.filter(([, value]) => value != null && value !== '');
  if (!visible.length) return '';
  return `<table>${visible
    .map(([label, value]) => `<tr><td class="label">${label}</td><td>${value}</td></tr>`)
    .join('')}</table>`;
}

function renderExifData(state) {
  const { srcUrl, result } = state;
  const { format, dimensions, exif } = result;

  let html = `<img class="thumb" src="${srcUrl}" alt="" />`;

  if (format === 'unsupported') {
    html += '<p class="empty">This image format isn\'t supported for metadata (JPEG, PNG, WebP, and TIFF are).</p>';
    content.innerHTML = html;
    return;
  }

  const imageRows = [
    ['Dimensions', dimensions ? `${dimensions.width} × ${dimensions.height}px` : null],
    ['Source URL', `<a href="${srcUrl}" target="_blank" rel="noopener noreferrer">${srcUrl}</a>`],
  ];
  html += `<section><h2>Image</h2>${formatRows(imageRows)}</section>`;

  if (!exif) {
    html += '<p class="empty">No EXIF metadata found (often stripped by social networks/CDNs on upload).</p>';
    content.innerHTML = html;
    return;
  }

  const cameraRows = [
    ['Make', exif.Make],
    ['Model', exif.Model],
    ['Lens', exif.LensModel],
    ['Software', exif.Software],
    ['Orientation', exif.Orientation != null ? ORIENTATIONS[exif.Orientation] || exif.Orientation : null],
  ];
  html += `<section><h2>Camera</h2>${formatRows(cameraRows) || '<p class="empty">None found.</p>'}</section>`;

  const shotRows = [
    ['Exposure time', formatExposureTime(exif.ExposureTime)],
    ['F-number', exif.FNumber != null ? `f/${exif.FNumber}` : null],
    ['ISO', exif.ISOSpeedRatings],
    ['Focal length', exif.FocalLength != null ? `${exif.FocalLength} mm` : null],
    ['Exposure program', exif.ExposureProgram != null ? EXPOSURE_PROGRAMS[exif.ExposureProgram] || exif.ExposureProgram : null],
    ['Flash', exif.Flash != null ? ((exif.Flash & 1) ? 'Fired' : 'Did not fire') : null],
    ['White balance', exif.WhiteBalance === 0 ? 'Auto' : exif.WhiteBalance === 1 ? 'Manual' : null],
    ['Color space', exif.ColorSpace === 1 ? 'sRGB' : exif.ColorSpace != null ? exif.ColorSpace : null],
  ];
  const shotHtml = formatRows(shotRows);
  if (shotHtml) html += `<section><h2>Shot settings</h2>${shotHtml}</section>`;

  const timeRows = [
    ['Taken', formatDateTime(exif.DateTimeOriginal)],
    ['Digitized', formatDateTime(exif.DateTimeDigitized)],
    ['File modified', formatDateTime(exif.DateTime)],
  ];
  const timeHtml = formatRows(timeRows);
  if (timeHtml) html += `<section><h2>Timestamps</h2>${timeHtml}</section>`;

  if (exif.GPSLatitude != null && exif.GPSLongitude != null) {
    const lat = exif.GPSLatitude.toFixed(6);
    const lon = exif.GPSLongitude.toFixed(6);
    const locationRows = [
      ['Coordinates', `${lat}, ${lon}`],
      ['Altitude', exif.GPSAltitude != null ? `${exif.GPSAltitude.toFixed(1)} m` : null],
      ['Direction', exif.GPSImgDirection != null ? `${exif.GPSImgDirection.toFixed(1)}°` : null],
      ['Date', exif.GPSDateStamp],
      [
        'Map',
        `<a href="https://www.google.com/maps?q=${lat},${lon}" target="_blank" rel="noopener noreferrer">Open in Google Maps</a>`,
      ],
    ];
    html += `<section><h2>Location</h2>${formatRows(locationRows)}</section>`;
  }

  content.innerHTML = html;
}

function renderExif(state) {
  if (!state) {
    content.className = 'loading';
    content.innerHTML = 'Right-click an image and choose "Show EXIF metadata".';
    return;
  }

  if (state.status === 'loading') {
    content.className = 'loading';
    content.textContent = 'Reading metadata…';
    return;
  }

  if (state.status === 'error') {
    content.className = 'error';
    content.textContent = state.message || 'Something went wrong.';
    return;
  }

  if (state.status === 'permission-denied') {
    content.className = 'error';
    content.innerHTML = '';
    const message = document.createElement('p');
    message.textContent = 'Reading this image needs one-time permission to access image data across sites.';
    const button = document.createElement('button');
    button.textContent = 'Grant access';
    button.addEventListener('click', async () => {
      const granted = await chrome.permissions.request({ origins: ['http://*/*', 'https://*/*'] });
      if (!granted) return;
      renderExif({ status: 'loading' });
      await chrome.runtime.sendMessage({ type: 'corvid-exif-retry', tabId: activeTabId, srcUrl: state.srcUrl });
    });
    content.append(message, button);
    return;
  }

  if (state.status === 'done') {
    content.className = '';
    renderExifData(state);
  }
}

// A stored EXIF entry newer than this is treated as "just triggered by a right-click just now"
// and auto-focuses the EXIF tab; anything older is stale from an earlier click on this tab and
// stays a click away instead of hijacking a toolbar-icon open that should default to Home.
const RECENT_MS = 5000;

async function loadForActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  activeTabId = tab?.id ?? null;
  if (activeTabId == null) return;

  const stored = await chrome.storage.session.get(`exif:${activeTabId}`);
  const state = stored[`exif:${activeTabId}`];
  renderExif(state);
  tabExifButton.disabled = !state;

  if (state && Date.now() - (state.updatedAt || 0) < RECENT_MS) {
    setView('exif');
  } else {
    setView('home');
  }
}

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== 'session' || activeTabId == null) return;
  const key = `exif:${activeTabId}`;
  if (!(key in changes)) return;
  renderExif(changes[key].newValue);
  tabExifButton.disabled = !changes[key].newValue;
  setView('exif'); // a storage update for this tab only ever happens from a fresh right-click
});

chrome.tabs.onActivated.addListener(loadForActiveTab);

initQuickLinks();
initSearch();
initSettings();
loadForActiveTab();
