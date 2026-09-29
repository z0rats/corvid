import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Confirms extension/generated-ioc-patterns.js (regenerated from iocTypeDetection.ts's
// IOC_TYPE_PATTERNS by frontend/scripts/generate-extension-ioc-patterns.js) still recognizes
// every case in the fixture backend/frontend already share - the extension previously had no
// test coverage for its IOC regexes at all, and its hand-copied table had already drifted
// (see docs/architecture/browser-extension.md).
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturePath = path.resolve(__dirname, '../../../../testdata/ioc-type-detection-cases.json');
const HAPPY_PATH_CASES = JSON.parse(fs.readFileSync(fixturePath, 'utf-8'));

const require = createRequire(import.meta.url);
const generatedPath = path.resolve(__dirname, '../../../../extension/generated-ioc-patterns.js');
const { GENERATED_IOC_TYPE_PATTERNS } = require(generatedPath);

describe('extension generated-ioc-patterns.js — shared fixture cross-check', () => {
  // "unknown" cases have no corresponding entry in GENERATED_IOC_TYPE_PATTERNS (it's a table of
  // real IOC-type regexes, not a full classifier) - covered instead by the extension's own
  // detectIocType, which layers priority order on top of this table.
  const POSITIVE_CASES = HAPPY_PATH_CASES.filter((c) => c.expectedType !== 'unknown');

  it.each(POSITIVE_CASES.map((c) => [c.value, c.expectedType]))(
    'classifies %j as %s',
    (value, expectedType) => {
      const pattern = GENERATED_IOC_TYPE_PATTERNS[expectedType];
      expect(pattern).toBeInstanceOf(RegExp);
      expect(pattern.test(value)).toBe(true);
    },
  );
});
