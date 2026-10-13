// Pattern syntax for handles whose structure the analyst partly knows: `john[._-]doe`,
// `john[0-9]{0-2}`, `[jJ]ohn`. Expands to a bounded list of candidates to pick from - never a
// bulk scan (one scan is already ~500 sites). Pure and offline.
//
//   [chars]       one character from the set; `a-z` ranges, `-` literal at either end
//   [chars]{n}    exactly n characters; `{n-m}` n to m, `{n;m}` n or m, `{0-2;5}` mixes both
//   \[ \] \\ \-   literal bracket / backslash / dash (outside a set, only `\[` `\]` `\\`)

export const MAX_PATTERN_SHOWN = 100;
// Above this many expansions the pattern is refused, so a careless `[a-z]{5}` (11.9M) can't
// stall the page and isn't mistaken for something worth scanning.
export const MAX_PATTERN_TOTAL = 10_000;

export type PatternError = 'syntax' | 'tooBroad';

export type PatternResult =
  | { ok: true; total: number; values: string[] }
  | { ok: false; error: PatternError; detail?: string };

type Block = string | { charset: string[]; lengths: number[] };

class PatternSyntaxError extends Error {}

/** True when the text uses a set (an unescaped `[`), i.e. should be read as a pattern. Walks
 *  escapes the way `parse` does, so `\\[a]` (a literal backslash, then a set) is a pattern. */
export function isPattern(input: string): boolean {
  for (let i = 0; i < input.length; i += 1) {
    if (input[i] === '\\') i += 1;
    else if (input[i] === '[') return true;
  }
  return false;
}

/** A handle typed with escapes but no set (`john\[x\]`) means the literal characters. */
export function unescapeLiterals(input: string): string {
  return input.replace(/\\([[\]\\])/g, '$1');
}

function parseLengths(spec: string): number[] {
  const lengths = new Set<number>();
  for (const part of spec.split(';')) {
    const range = /^(\d{1,2})(?:-(\d{1,2}))?$/.exec(part.trim());
    if (!range) throw new PatternSyntaxError(`bad length "${spec}"`);
    const low = Number(range[1]);
    const high = range[2] === undefined ? low : Number(range[2]);
    if (high < low) throw new PatternSyntaxError(`descending length "${part}"`);
    for (let n = low; n <= high; n += 1) lengths.add(n);
  }
  return [...lengths].sort((a, b) => a - b);
}

function parseSet(body: string): string[] {
  const chars = new Set<string>();
  const items = [...body];
  for (let i = 0; i < items.length; i += 1) {
    let ch = items[i];
    if (ch === '\\') {
      i += 1;
      if (i >= items.length) throw new PatternSyntaxError('dangling "\\"');
      ch = items[i];
      chars.add(ch);
    } else if (items[i + 1] === '-' && i + 2 < items.length) {
      const end = items[i + 2];
      if (end.charCodeAt(0) < ch.charCodeAt(0)) throw new PatternSyntaxError(`descending range "${ch}-${end}"`);
      for (let code = ch.charCodeAt(0); code <= end.charCodeAt(0); code += 1) chars.add(String.fromCharCode(code));
      i += 2;
    } else {
      chars.add(ch);
    }
  }
  if (chars.size === 0) throw new PatternSyntaxError('empty set');
  return [...chars].sort();
}

function parse(input: string): Block[] {
  const blocks: Block[] = [];
  const pushLiteral = (ch: string) => {
    const last = blocks[blocks.length - 1];
    if (typeof last === 'string') blocks[blocks.length - 1] = last + ch;
    else blocks.push(ch);
  };
  let i = 0;
  while (i < input.length) {
    const ch = input[i];
    if (ch === '\\') {
      const next = input[i + 1];
      if (next === undefined || !'[]\\'.includes(next)) throw new PatternSyntaxError('bad escape');
      pushLiteral(next);
      i += 2;
    } else if (ch === '[') {
      let j = i + 1;
      while (j < input.length && input[j] !== ']') j += input[j] === '\\' ? 2 : 1;
      if (j >= input.length) throw new PatternSyntaxError('missing "]"');
      const charset = parseSet(input.slice(i + 1, j));
      i = j + 1;
      let lengths = [1];
      if (input[i] === '{') {
        const close = input.indexOf('}', i);
        if (close === -1) throw new PatternSyntaxError('missing "}"');
        lengths = parseLengths(input.slice(i + 1, close));
        i = close + 1;
      }
      blocks.push({ charset, lengths });
    } else if (ch === ']' || ch === '{' || ch === '}') {
      throw new PatternSyntaxError(`unexpected "${ch}"`);
    } else {
      pushLiteral(ch);
      i += 1;
    }
  }
  return blocks;
}

function blockSize(block: Block): number {
  if (typeof block === 'string') return 1;
  return block.lengths.reduce((sum, n) => sum + block.charset.length ** n, 0);
}

function* expandBlock(block: Block): Generator<string> {
  if (typeof block === 'string') {
    yield block;
    return;
  }
  for (const length of block.lengths) {
    const indices = new Array<number>(length).fill(0);
    for (;;) {
      yield indices.map((idx) => block.charset[idx]).join('');
      let pos = length - 1;
      while (pos >= 0 && indices[pos] === block.charset.length - 1) {
        indices[pos] = 0;
        pos -= 1;
      }
      if (pos < 0) break;
      indices[pos] += 1;
    }
  }
}

function* expandAll(blocks: Block[], from = 0): Generator<string> {
  if (from === blocks.length) {
    yield '';
    return;
  }
  for (const head of expandBlock(blocks[from])) {
    for (const tail of expandAll(blocks, from + 1)) yield head + tail;
  }
}

/** Expand a pattern into at most `limit` candidates; `total` is the full count, known up front. */
export function expandPattern(input: string, limit = MAX_PATTERN_SHOWN): PatternResult {
  let blocks: Block[];
  try {
    blocks = parse(input.trim());
  } catch (error) {
    if (error instanceof PatternSyntaxError) return { ok: false, error: 'syntax', detail: error.message };
    throw error;
  }
  const total = blocks.reduce((product, block) => product * blockSize(block), 1);
  if (total > MAX_PATTERN_TOTAL) return { ok: false, error: 'tooBroad' };

  const values: string[] = [];
  const seen = new Set<string>();
  for (const value of expandAll(blocks)) {
    if (seen.has(value)) continue;
    seen.add(value);
    if (values.length < limit) values.push(value);
  }
  return { ok: true, total: seen.size, values };
}
