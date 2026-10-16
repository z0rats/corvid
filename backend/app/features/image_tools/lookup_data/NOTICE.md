# Data provenance

Derived from [GeoInt](https://github.com/marouane53/GeoINT) (MIT) and
[geo-sleuth](https://github.com/Oldcircle/geo-sleuth) (MIT, Oldcircle). Their license texts,
with the copyright notices MIT requires to be kept, are in `LICENSE-GeoInt.txt` and
`LICENSE-geo-sleuth.txt` next to this file.

- `text_signals.json` - scripts, digits, language-specific letters, currency marks, vanity TLDs and
  regional signage words. MIT. The GeoInt `hanzi` block is omitted.
- `country_info.json` - name, TLD, calling code, postal regex and languages per ISO-3166 alpha-2
  code. Compact extract of GeoInt's `countries.json`, built from
  [GeoNames](https://www.geonames.org/) `countryInfo.txt` (CC BY 4.0, © GeoNames). GeoInt's
  driving-side column is deliberately left out: it is Wikipedia-derived (CC BY-SA 4.0), and the
  same fact already comes from `country_clues.json` below under MIT.
- `country_clues.json` - one row per country (driving side, plates, road paint, script, other
  strong tells) taken from the "Quick table" of each file in GeoInt's `references/world/`
  (europe, americas, asia, oceania, africa-middle-east). MIT. General knowledge, not proof.
