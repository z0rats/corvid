// Regional-indicator emoji flag for an ISO 3166-1 alpha-2 code; renders nothing for anything else.
const REGIONAL_INDICATOR_A = 0x1f1e6;

function countryCodeToFlag(code) {
  if (typeof code !== 'string' || !/^[a-z]{2}$/i.test(code)) return null;
  return String.fromCodePoint(
    ...[...code.toUpperCase()].map((ch) => REGIONAL_INDICATOR_A + ch.charCodeAt(0) - 65)
  );
}

export default function CountryFlag({ countryCode, title }) {
  const flag = countryCodeToFlag(countryCode);
  if (!flag) return null;
  const label = title || countryCode.toUpperCase();
  return (
    <span role="img" aria-label={label} title={label}>
      {flag}
    </span>
  );
}
