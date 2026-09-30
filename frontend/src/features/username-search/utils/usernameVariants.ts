// Heuristic "other handles this person might use" suggestions for a typed username. Pure and
// offline (no requests) - people reuse a handle with small tweaks (separator, trailing year,
// first.last -> flast, leetspeak), so each rule below models one such habit. Suggestions are
// hypotheses to search, not attribution: any hit still needs manual verification.

export type VariantReason =
  | 'separator'
  | 'digits'
  | 'nameOrder'
  | 'nickname'
  | 'leet'
  | 'affix';

export interface UsernameVariant {
  value: string;
  reason: VariantReason;
}

export const MAX_VARIANTS = 40;

const JOINERS = ['', '.', '_', '-'];
const VALID_HANDLE = /^[a-z0-9][a-z0-9._-]{1,38}[a-z0-9]$/;

// Small on purpose: common English short forms plus the Latin transliterations most seen for
// Russian-speaking users. Keys are full names, values are diminutives; lookup goes both ways.
const NICKNAME_GROUPS: string[][] = [
  ['john', 'johny', 'johnny', 'jon', 'jack'],
  ['michael', 'mike', 'misha', 'mick'],
  ['william', 'will', 'bill', 'billy', 'liam'],
  ['robert', 'rob', 'bob', 'bobby'],
  ['richard', 'rick', 'rich', 'dick'],
  ['james', 'jim', 'jimmy'],
  ['alexander', 'alex', 'sasha', 'sanya'],
  ['alexey', 'alex', 'lesha', 'alyosha'],
  ['dmitry', 'dmitri', 'dima', 'dimon'],
  ['sergey', 'sergei', 'serega', 'serzh'],
  ['andrey', 'andrei', 'andrew', 'andy', 'andryusha'],
  ['nikolay', 'nikolai', 'nick', 'kolya'],
  ['vladimir', 'vova', 'vlad', 'volodya'],
  ['ivan', 'vanya', 'vanek'],
  ['maxim', 'max', 'maks'],
  ['anastasia', 'nastya', 'stacy', 'ana'],
  ['elizabeth', 'liz', 'beth', 'eliza', 'lisa'],
  ['katherine', 'kate', 'katya', 'katie', 'kat'],
  ['daniel', 'dan', 'danny', 'danya'],
  ['christopher', 'chris', 'kris'],
  ['matthew', 'matt', 'matvey'],
  ['thomas', 'tom', 'tommy'],
  ['anthony', 'tony', 'anton'],
  ['joseph', 'joe', 'joey'],
  ['edward', 'ed', 'eddie', 'ted'],
];

const LEET_FORWARD: Record<string, string> = { o: '0', i: '1', l: '1', e: '3', a: '4', s: '5', t: '7' };
const LEET_REVERSE: Record<string, string> = {
  '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', $: 's',
};

const AFFIXES = { prefix: ['the', 'real', 'mr'], suffix: ['official', 'real', 'dev', 'x'] };

/** Splits on separators, camelCase humps and letter/digit boundaries: "JohnSmith_90" -> john, smith, 90. */
export function tokenize(input: string): string[] {
  return input
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/([a-zA-Z])(\d)/g, '$1 $2')
    .replace(/(\d)([a-zA-Z])/g, '$1 $2')
    .split(/[^a-zA-Z0-9]+/)
    .filter(Boolean)
    .map((token) => token.toLowerCase());
}

/** An email pasted into the username box: search by its local part, minus any +tag. */
function stripEmail(input: string): string {
  const at = input.indexOf('@');
  if (at <= 0 || input.indexOf('.', at) === -1) return input;
  return input.slice(0, at).split('+')[0];
}

const isAlpha = (token: string) => /^[a-z]+$/.test(token);
const isDigits = (token: string) => /^\d+$/.test(token);

function separatorVariants(tokens: string[]): string[] {
  if (tokens.length < 2) return [];
  return JOINERS.map((joiner) => tokens.join(joiner));
}

function digitVariants(tokens: string[]): string[] {
  const last = tokens[tokens.length - 1];
  if (tokens.length < 2 || !isDigits(last)) return [];
  const base = tokens.slice(0, -1);
  const out = JOINERS.map((joiner) => base.join(joiner));
  // 4-digit birth year <-> its 2-digit short form, the most common way people vary a suffix.
  if (/^(19|20)\d\d$/.test(last)) {
    out.push(`${base.join('')}${last.slice(2)}`, `${base.join('_')}_${last.slice(2)}`);
  } else if (last.length === 2) {
    const century = Number(last) > 30 ? '19' : '20';
    out.push(`${base.join('')}${century}${last}`);
  }
  return out;
}

function nameOrderVariants(tokens: string[]): string[] {
  const words = tokens.filter(isAlpha);
  if (tokens.length !== words.length || words.length !== 2) return [];
  const [first, last] = words;
  const out: string[] = [];
  for (const joiner of JOINERS) {
    out.push(`${last}${joiner}${first}`, `${first[0]}${joiner}${last}`, `${first}${joiner}${last[0]}`);
    out.push(`${last[0]}${joiner}${first}`, `${last}${joiner}${first[0]}`);
  }
  return out;
}

function nicknameVariants(tokens: string[]): string[] {
  const out: string[] = [];
  tokens.forEach((token, index) => {
    if (!isAlpha(token)) return;
    const group = NICKNAME_GROUPS.filter((names) => names.includes(token));
    for (const alias of new Set(group.flat())) {
      if (alias === token) continue;
      const swapped = tokens.map((t, i) => (i === index ? alias : t));
      out.push(swapped.join(''), swapped.join('_'), swapped.join('.'));
    }
  });
  return out;
}

function leetVariants(base: string): string[] {
  const out: string[] = [];
  // Un-leet the whole handle, then leet one character at a time (a full swap is rarely typed).
  if (/[0-9@$]/.test(base)) {
    out.push(base.replace(/[0-9@$]/g, (ch) => LEET_REVERSE[ch] ?? ch));
  }
  for (let i = 0; i < base.length; i += 1) {
    const sub = LEET_FORWARD[base[i]];
    if (sub) out.push(base.slice(0, i) + sub + base.slice(i + 1));
  }
  return out;
}

function affixVariants(base: string): string[] {
  return [
    ...AFFIXES.prefix.map((p) => `${p}${base}`),
    ...AFFIXES.suffix.map((s) => `${base}_${s}`),
    `_${base}`,
    `${base}_`,
  ];
}

/** Ordered by how often people actually pick each pattern - cap cuts off the noisy tail. */
export function generateUsernameVariants(input: string, limit = MAX_VARIANTS): UsernameVariant[] {
  const raw = stripEmail(input.trim());
  const original = raw.toLowerCase();
  const tokens = tokenize(raw);
  if (tokens.length === 0) return [];
  const compact = tokens.join('');

  const candidates: Array<[VariantReason, string[]]> = [
    ['separator', separatorVariants(tokens)],
    ['digits', digitVariants(tokens)],
    ['nameOrder', nameOrderVariants(tokens)],
    ['nickname', nicknameVariants(tokens)],
    ['leet', leetVariants(compact)],
    ['affix', affixVariants(compact)],
  ];

  const seen = new Set<string>([original]);
  const variants: UsernameVariant[] = [];
  for (const [reason, values] of candidates) {
    for (const value of values) {
      if (seen.has(value) || !VALID_HANDLE.test(value)) continue;
      seen.add(value);
      variants.push({ value, reason });
    }
  }

  // Round-robin across reasons before capping so one prolific rule (nickname, leet) can't
  // crowd out every other kind of suggestion.
  const byReason = new Map<VariantReason, UsernameVariant[]>();
  variants.forEach((v) => byReason.set(v.reason, [...(byReason.get(v.reason) ?? []), v]));
  const queues = [...byReason.values()];
  const balanced: UsernameVariant[] = [];
  while (balanced.length < limit && queues.some((q) => q.length)) {
    for (const queue of queues) {
      const next = queue.shift();
      if (next && balanced.length < limit) balanced.push(next);
    }
  }
  return balanced;
}
