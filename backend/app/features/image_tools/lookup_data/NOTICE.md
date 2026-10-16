# Data provenance

Derived from [GeoInt](https://github.com/marouane53/GeoINT) (MIT) and
[geo-sleuth](https://github.com/Oldcircle/geo-sleuth) (MIT, Oldcircle).

- `text_signals.json` - scripts, digits, language-specific letters, currency marks, vanity TLDs and
  regional signage words. MIT. The GeoInt `hanzi` block is omitted.
- `country_info.json` - name, TLD, calling code, postal regex, languages and driving side per
  ISO-3166 alpha-2 code. Compact extract of GeoInt's `countries.json`, built from
  [GeoNames](https://www.geonames.org/) `countryInfo.txt` (CC BY 4.0) plus Wikipedia-derived
  driving-side data (CC BY-SA 4.0).
- `country_clues.json` - one row per country (driving side, plates, road paint, script, other
  strong tells) taken from the "Quick table" of each file in GeoInt's `references/world/`
  (europe, americas, asia, oceania, africa-middle-east). MIT. General knowledge, not proof.
