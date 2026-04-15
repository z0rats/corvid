export function collectAllIOCs(extractedData) {
  if (!extractedData) return [];

  return [
    ...(extractedData.domains || []),
    ...(extractedData.ips || []),
    ...(extractedData.urls || []),
    ...(extractedData.emails || []),
    ...(extractedData.md5 || []),
    ...(extractedData.sha1 || []),
    ...(extractedData.sha256 || []),
    ...(extractedData.cves || [])
  ];
}

export async function copyIOCsToClipboard(iocs) {
  if (!iocs || iocs.length === 0) {
    throw new Error('No IOCs to copy');
  }

  await navigator.clipboard.writeText(iocs.join('\n'));
  return { count: iocs.length, message: `Copied ${iocs.length} IOCs to clipboard` };
}

export function exportIOCsToFile(iocs, filename = 'extracted_iocs') {
  if (!iocs || iocs.length === 0) {
    throw new Error('No IOCs to export');
  }

  const blob = new Blob([iocs.join('\n')], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `${filename}_${new Date().toISOString().split('T')[0]}.txt`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);

  return { count: iocs.length, message: `Exported ${iocs.length} IOCs to file` };
}

const IOC_TYPE_MAP = {
  ipv4: 'IPv4',
  ipv6: 'IPv6',
  domain: 'Domain',
  url: 'URL',
  email: 'Email',
  md5: 'MD5',
  sha1: 'SHA1',
  sha256: 'SHA256'
};

export function mapIocTypeToLabel(type) {
  return IOC_TYPE_MAP[type] || 'MD5';
}
