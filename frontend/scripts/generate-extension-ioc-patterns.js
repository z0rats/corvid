#!/usr/bin/env node
/**
 * Regenerates extension/generated-ioc-patterns.js from
 * src/core/utils/iocTypeDetection.ts's IOC_TYPE_PATTERNS, so the extension's IOC-type
 * regexes can't silently drift from the frontend's (see docs/architecture/browser-extension.md).
 *
 * The extension has no build step and loads plain classic scripts, so this doesn't bundle
 * iocTypeDetection.ts itself - it strips its types via the TypeScript compiler (already a
 * project dependency), evaluates the resulting module to get real, already-resolved RegExp
 * values, and serializes just the pattern table as a standalone .js file. The extension's own
 * detectIocType (phone-in-chain, trailing-punctuation stripping) stays hand-written and reads
 * from this generated table instead of declaring its own copy.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const ts = require('typescript');

const SOURCE_PATH = path.join(__dirname, '..', 'src', 'core', 'utils', 'iocTypeDetection.ts');
const OUTPUT_PATH = path.join(__dirname, '..', '..', 'extension', 'generated-ioc-patterns.js');

function loadIocTypePatterns() {
  const source = fs.readFileSync(SOURCE_PATH, 'utf-8');
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  });

  // IOC_TYPE_PATTERNS is intentionally module-private in iocTypeDetection.ts (not part of its
  // public interface) - force-export the local binding so this script can read it without
  // widening that file's actual exports.
  const withPatternsExported = `${outputText}\nmodule.exports.IOC_TYPE_PATTERNS = IOC_TYPE_PATTERNS;\n`;

  const tmpFile = path.join(os.tmpdir(), `ioc-type-detection-${Date.now()}.cjs`);
  fs.writeFileSync(tmpFile, withPatternsExported);
  try {
    const mod = require(tmpFile);
    return mod.IOC_TYPE_PATTERNS;
  } finally {
    fs.unlinkSync(tmpFile);
  }
}

function serializePatterns(patterns) {
  const lines = Object.entries(patterns).map(([key, regex]) => `  ${key}: ${regex.toString()},`);
  return `{\n${lines.join('\n')}\n}`;
}

function main() {
  const patterns = loadIocTypePatterns();
  const banner = `// GENERATED FILE - DO NOT EDIT BY HAND.
// Regenerate with: node frontend/scripts/generate-extension-ioc-patterns.js
// Source of truth: frontend/src/core/utils/iocTypeDetection.ts's IOC_TYPE_PATTERNS.
// A pre-commit hook regenerates this automatically when that file changes; CI fails if
// this file is stale (see docs/architecture/browser-extension.md).
`;
  const body = `const GENERATED_IOC_TYPE_PATTERNS = ${serializePatterns(patterns)};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { GENERATED_IOC_TYPE_PATTERNS };
}
`;

  fs.writeFileSync(OUTPUT_PATH, banner + '\n' + body);
  console.log(`Wrote ${path.relative(process.cwd(), OUTPUT_PATH)}`);
}

main();
