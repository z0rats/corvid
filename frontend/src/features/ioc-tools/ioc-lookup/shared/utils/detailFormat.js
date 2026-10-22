// Formatting shared by the IOC lookup provider cards.

// Locale date for an ISO timestamp; '' when there is none, so a table cell stays empty.
export const formatDate = (value) => (value ? new Date(value).toLocaleDateString() : '');

// "vendor product version" for a Censys software attribute, dropping a vendor that just
// repeats the product ("cloudflare cloudflare" -> "cloudflare").
export const softwareLabel = ({ vendor, product, version }) => {
  const name = product && vendor && product.toLowerCase() !== vendor.toLowerCase()
    ? `${vendor} ${product}`
    : product || vendor;
  return version ? `${name} ${version}` : name;
};

// Censys tags software with its own classification (`types`); a WAF is what the card highlights.
export const isWaf = (software) => (software.types || []).some((type) => /waf/i.test(type));
