// Client-side JSON/CSV export of a history record - the data is already in the browser, so no
// backend report endpoint is needed for features that don't have one.

// Leading characters spreadsheet apps treat as a formula. Values come from scanned third-party
// content (profile names, post titles), so they're neutralized rather than trusted.
const FORMULA_PREFIX_RE = /^[=+\-@\t\r]/;

function toCell(value) {
  if (value === null || value === undefined) return '';
  let text = typeof value === 'object' ? JSON.stringify(value) : String(value);
  if (FORMULA_PREFIX_RE.test(text)) text = `'${text}`;
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/** Rows of (shallow) objects -> CSV; columns are the union of keys in first-seen order. */
export function toCsv(rows) {
  const columns = [];
  rows.forEach((row) => Object.keys(row).forEach((key) => {
    if (!columns.includes(key)) columns.push(key);
  }));
  const lines = [columns.map(toCell).join(',')];
  rows.forEach((row) => lines.push(columns.map((col) => toCell(row[col])).join(',')));
  return `${lines.join('\r\n')}\r\n`;
}

/** A filesystem-safe base name from a run's target, e.g. "amass-example.com-12". */
export function exportFileName(...parts) {
  return parts
    .filter((part) => part !== null && part !== undefined && part !== '')
    .join('-')
    .replace(/[^\w.@-]+/g, '_')
    .slice(0, 120);
}

export function downloadFile(content, fileName, mimeType) {
  const url = URL.createObjectURL(new Blob([content], { type: mimeType }));
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export const downloadJson = (data, baseName) => downloadFile(
  JSON.stringify(data, null, 2), `${baseName}.json`, 'application/json',
);

export const downloadCsv = (rows, baseName) => downloadFile(
  // BOM so Excel opens non-ASCII (Cyrillic etc.) as UTF-8.
  `\uFEFF${toCsv(rows)}`, `${baseName}.csv`, 'text/csv;charset=utf-8',
);
