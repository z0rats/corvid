const DEFAULT_BASE_URL = 'http://localhost:4000';

const input = document.getElementById('baseUrl');
const status = document.getElementById('status');

chrome.storage.local.get('corvidBaseUrl').then(({ corvidBaseUrl }) => {
  input.value = corvidBaseUrl || DEFAULT_BASE_URL;
});

document.getElementById('save').addEventListener('click', async () => {
  const value = input.value.trim().replace(/\/$/, '') || DEFAULT_BASE_URL;
  await chrome.storage.local.set({ corvidBaseUrl: value });
  input.value = value;
  status.textContent = 'Saved.';
  setTimeout(() => {
    status.textContent = '';
  }, 1500);
});
