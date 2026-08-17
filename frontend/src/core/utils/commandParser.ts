import { detectIocType, IOC_TYPES, isYoutubeVideoUrl, type IocType } from './iocTypeDetection';

/**
 * Pure, framework-free parsing of the command palette's input grammar (see
 * docs/command-palette-plan.md's "Interaction grammar" table). Every function here takes plain
 * data in and returns plain data out — no DOM, no storage, no network — so it's fully covered by
 * Vitest without rendering anything. The stateful pieces (recording sessions, storage,
 * navigation, clipboard, network) live in core/hooks/useCommandPalette.ts instead.
 */

// Registry entries are built by commandRegistry.js (plain JS, derived from sidebarConfig.jsx) and
// passed in by each palette host - modeled here rather than imported, so this file's types don't
// force those still-JS/JSX modules to convert first.
export interface RegistryEntry {
  id: string;
  label: string;
  icon?: unknown;
  path: string;
  moduleId: string;
  aliases: string[];
  tags: string[];
  accepts: IocType[];
  acceptsRouting: Record<string, string>;
}

export interface Playbook {
  name: string;
  [key: string]: unknown;
}

export interface ParserContext {
  registry: RegistryEntry[];
  playbooks: Playbook[];
  isRecording: boolean;
}

// Friendly `type:kind` tokens -> one or more iocTypeDetection.ts type strings.
export const TYPE_TOKEN_ALIASES: Record<string, IocType[]> = {
  ip: [IOC_TYPES.IPV4, IOC_TYPES.IPV6],
  ipv4: [IOC_TYPES.IPV4],
  ipv6: [IOC_TYPES.IPV6],
  domain: [IOC_TYPES.DOMAIN],
  url: [IOC_TYPES.URL],
  email: [IOC_TYPES.EMAIL],
  hash: [IOC_TYPES.MD5, IOC_TYPES.SHA1, IOC_TYPES.SHA256],
  youtube: [IOC_TYPES.YOUTUBE_VIDEO_URL],
  md5: [IOC_TYPES.MD5],
  sha1: [IOC_TYPES.SHA1],
  sha256: [IOC_TYPES.SHA256],
  cve: [IOC_TYPES.CVE],
  crypto: [
    IOC_TYPES.EVM_ADDRESS, IOC_TYPES.BITCOIN_ADDRESS, IOC_TYPES.TRON_ADDRESS,
    IOC_TYPES.XRP_ADDRESS, IOC_TYPES.DOGECOIN_ADDRESS, IOC_TYPES.LITECOIN_ADDRESS,
    IOC_TYPES.STELLAR_ADDRESS, IOC_TYPES.BINANCE_CHAIN_ADDRESS, IOC_TYPES.LISK_ADDRESS,
    IOC_TYPES.CARDANO_ADDRESS,
  ],
  btc: [IOC_TYPES.BITCOIN_ADDRESS],
  eth: [IOC_TYPES.EVM_ADDRESS],
  tron: [IOC_TYPES.TRON_ADDRESS],
  xrp: [IOC_TYPES.XRP_ADDRESS],
  doge: [IOC_TYPES.DOGECOIN_ADDRESS],
  ltc: [IOC_TYPES.LITECOIN_ADDRESS],
  xlm: [IOC_TYPES.STELLAR_ADDRESS],
  bnb: [IOC_TYPES.BINANCE_CHAIN_ADDRESS],
  lsk: [IOC_TYPES.LISK_ADDRESS],
  ada: [IOC_TYPES.CARDANO_ADDRESS],
};

// `>` quick actions that don't depend on saved playbooks/recording state.
export const BUILTIN_ACTIONS = ['settings', 'theme', 'record', 'playbook:manage'];

// Parsed kinds whose `.value` is a real typed value (as opposed to `.query`/no value at all) —
// consumed anywhere a focused row's value can be copied, bulk-added, or handed off as a pivot.
export const VALUE_KINDS = ['value', 'pivot', 'fallback'];

function normalize(value?: string | null): string {
  return (value ?? '').toLowerCase().trim();
}

/** Case-insensitive substring/prefix scoring against a registry entry's label/aliases/tags. */
function scoreMatch(query: string, entry: RegistryEntry): number {
  const q = normalize(query);
  if (!q) return 0;

  const candidates = [entry.label, ...entry.aliases, ...entry.tags].map(normalize);
  let best = 0;
  candidates.forEach((candidate) => {
    if (candidate === q) best = Math.max(best, 100);
    else if (candidate.startsWith(q)) best = Math.max(best, 80);
    else if (candidate.includes(q)) best = Math.max(best, 50);
  });
  return best;
}

/** Fuzzy-matches a query against registry entries' name/aliases/tags, best match first. */
export function matchTools(query: string, registry: RegistryEntry[]): RegistryEntry[] {
  return registry
    .map((entry) => ({ entry, score: scoreMatch(query, entry) }))
    .filter((m) => m.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((m) => m.entry);
}

/** Registry entries whose `accepts` includes the given detected IOC type. */
export function rankToolsForValue(iocType: IocType, registry: RegistryEntry[]): RegistryEntry[] {
  return registry.filter((entry) => entry.accepts.includes(iocType));
}

export function resolvePlaybook(name: string, playbooks: Playbook[]): Playbook | null {
  return playbooks.find((p) => p.name === name) ?? null;
}

export type WhichKeyOperator = '#' | 'type:' | '>';

/**
 * Empty-operator "which-key" completions: typing a bare `#`, `type:`, or `>` always lists
 * everything valid to type next (see docs/command-palette-plan.md's which-key rule).
 */
export function getWhichKeySuggestions(
  operator: WhichKeyOperator,
  { registry = [], playbooks = [], isRecording = false }: Partial<ParserContext> = {},
): string[] {
  if (operator === '#') {
    const tags = new Set<string>();
    registry.forEach((entry) => entry.tags.forEach((tag) => tags.add(tag)));
    return [...tags].sort();
  }
  if (operator === 'type:') {
    return Object.keys(TYPE_TOKEN_ALIASES).sort();
  }
  if (operator === '>') {
    const actions = [...BUILTIN_ACTIONS];
    if (isRecording) actions.push('record:stop');
    playbooks.forEach((p) => actions.push(`playbook:${p.name}`));
    return actions;
  }
  return [];
}

export interface WhichKeyParsed {
  kind: 'which-key';
  operator: WhichKeyOperator;
  suggestions: string[];
}

export interface TagParsed {
  kind: 'tag';
  tag: string;
  matches: RegistryEntry[];
}

export interface TypeParsed {
  kind: 'type';
  typeToken: string;
  iocTypes: IocType[];
  matches: RegistryEntry[];
}

export interface ActionParsed {
  kind: 'action';
  action: 'settings' | 'theme' | 'record-start' | 'record-stop' | 'playbook-manage' | 'playbook-run' | 'unknown';
  name?: string | null;
  raw?: string;
  playbookName?: string;
  value?: string | null;
}

export interface InstantParsed {
  kind: 'instant';
  op: string;
  value: string;
}

export interface ValueParsed {
  kind: 'value';
  value: string;
  iocType: IocType;
  matches: RegistryEntry[];
}

export interface PivotParsed {
  kind: 'pivot';
  value: string;
  tool: RegistryEntry;
  matches: RegistryEntry[];
}

export interface FallbackParsed {
  kind: 'fallback';
  value: string;
  matches: RegistryEntry[];
}

export interface TextParsed {
  kind: 'text';
  query: string;
  matches: RegistryEntry[];
}

export interface EmptyParsed {
  kind: 'empty';
}

export type ParsedQuery =
  | EmptyParsed
  | WhichKeyParsed
  | TagParsed
  | TypeParsed
  | ActionParsed
  | InstantParsed
  | ValueParsed
  | PivotParsed
  | FallbackParsed
  | TextParsed;

function parseHashTag(input: string, ctx: ParserContext): WhichKeyParsed | TagParsed {
  const tagText = input.slice(1).trim();
  if (!tagText) {
    return { kind: 'which-key', operator: '#', suggestions: getWhichKeySuggestions('#', ctx) };
  }
  const tag = tagText.toLowerCase();
  const matches = ctx.registry.filter((entry) => entry.tags.includes(tag));
  return { kind: 'tag', tag, matches };
}

function parseTypeFilter(input: string, ctx: ParserContext): WhichKeyParsed | TypeParsed {
  const token = input.slice('type:'.length).trim();
  if (!token) {
    return { kind: 'which-key', operator: 'type:', suggestions: getWhichKeySuggestions('type:', ctx) };
  }
  const typeToken = token.toLowerCase();
  const iocTypes = TYPE_TOKEN_ALIASES[typeToken] ?? [];
  const matches = ctx.registry.filter((entry) => entry.accepts.some((t) => iocTypes.includes(t)));
  return { kind: 'type', typeToken, iocTypes, matches };
}

function parseAction(input: string, ctx: ParserContext): WhichKeyParsed | ActionParsed {
  const rest = input.slice(1).trim();
  if (!rest) {
    return { kind: 'which-key', operator: '>', suggestions: getWhichKeySuggestions('>', ctx) };
  }

  const lower = rest.toLowerCase();

  if (lower === 'settings') return { kind: 'action', action: 'settings' };
  if (lower === 'theme') return { kind: 'action', action: 'theme' };
  if (lower === 'record') return { kind: 'action', action: 'record-start' };

  if (lower.startsWith('record:stop')) {
    const name = rest.slice('record:stop'.length).trim();
    return { kind: 'action', action: 'record-stop', name: name || null };
  }

  if (lower === 'playbook:manage') return { kind: 'action', action: 'playbook-manage' };

  if (lower.startsWith('playbook:')) {
    const after = rest.slice('playbook:'.length).trim();
    if (!after) {
      return {
        kind: 'which-key',
        operator: '>',
        suggestions: ctx.playbooks.map((p) => `playbook:${p.name}`),
      };
    }
    const [name, ...valueParts] = after.split(/\s+/);
    const value = valueParts.join(' ').trim();
    return { kind: 'action', action: 'playbook-run', playbookName: name, value: value || null };
  }

  return { kind: 'action', action: 'unknown', raw: rest };
}

function parseInstantAnswer(input: string): InstantParsed | null {
  const tokens = input.trim().split(/\s+/);
  const op = tokens[0]?.toLowerCase();
  if ((op === 'defang' || op === 'fang') && tokens.length > 1) {
    return { kind: 'instant', op, value: tokens.slice(1).join(' ') };
  }
  return null;
}

/**
 * Tries the tool name at either end of the input — "value tool" (the original convention here)
 * and "tool value" (the more common order elsewhere, e.g. Alfred/Raycast: action first, then its
 * argument) — so `john_doe reddit` and `reddit john_doe` both pivot the same way. "value tool" is
 * tried first for backward compatibility where a query happens to parse both ways.
 */
function parsePivot(input: string, ctx: ParserContext): PivotParsed | null {
  const tokens = input.trim().split(/\s+/);
  if (tokens.length < 2) return null;

  const trailingMatches = matchTools(tokens[tokens.length - 1], ctx.registry);
  if (trailingMatches.length > 0) {
    return { kind: 'pivot', value: tokens.slice(0, -1).join(' '), tool: trailingMatches[0], matches: trailingMatches };
  }

  const leadingMatches = matchTools(tokens[0], ctx.registry);
  if (leadingMatches.length > 0) {
    return { kind: 'pivot', value: tokens.slice(1).join(' '), tool: leadingMatches[0], matches: leadingMatches };
  }

  return null;
}

/**
 * Fallback for a typed value that matched no tool by name and no recognized IOC type — rather
 * than a dead-end "no matches" (Corvid's original behavior), offer the registry's `identity`-
 * tagged tools as pivot targets, à la Alfred/Raycast's fallback web-search actions. The only real
 * ranking signal available for an arbitrary string is a loose shape check — an `@` promotes
 * email-search, since nothing else in the identity group is email-shaped; beyond that, a bare
 * username-like token (e.g. a Reddit vs. GitHub handle) is equally plausible for every remaining
 * candidate, so there's nothing left to rank on and registry order stands.
 */
function rankIdentityFallback(value: string, registry: RegistryEntry[]): RegistryEntry[] {
  const candidates = registry.filter((entry) => entry.tags.includes('identity'));
  if (candidates.length === 0) return [];
  if (!value.includes('@')) return candidates;
  return [...candidates].sort((a, b) => Number(b.tags.includes('email')) - Number(a.tags.includes('email')));
}

export type SelectableResult = { type: 'suggestion'; value: string } | { type: 'entry'; entry: RegistryEntry };

/**
 * Parses raw palette input into a discriminated result. `ctx` carries the data the pure parser
 * needs but shouldn't own itself: { registry, playbooks, isRecording }.
 */
/** Everything the currently parsed query can offer as a keyboard-selectable row. */
export function getSelectableResults(parsed: ParsedQuery): SelectableResult[] {
  if (parsed.kind === 'which-key') {
    return parsed.suggestions.map((s) => ({ type: 'suggestion' as const, value: s }));
  }
  if (parsed.kind === 'text' || parsed.kind === 'tag' || parsed.kind === 'type'
    || parsed.kind === 'value' || parsed.kind === 'pivot' || parsed.kind === 'fallback') {
    return parsed.matches.map((entry) => ({ type: 'entry' as const, entry }));
  }
  return [];
}

export function parseQuery(rawInput?: string | null, ctx: Partial<ParserContext> = {}): ParsedQuery {
  const context: ParserContext = { registry: [], playbooks: [], isRecording: false, ...ctx };
  const input = (rawInput ?? '').trim();

  if (!input) return { kind: 'empty' };

  if (input.startsWith('#')) return parseHashTag(input, context);
  if (input.toLowerCase().startsWith('type:')) return parseTypeFilter(input, context);
  if (input.startsWith('>')) return parseAction(input, context);

  const instant = parseInstantAnswer(input);
  if (instant) return instant;

  const iocType = detectIocType(input);
  if (iocType !== IOC_TYPES.UNKNOWN) {
    const matches = rankToolsForValue(iocType, context.registry);
    // detectIocType classifies a YouTube link as plain URL (see iocTypeDetection.ts's
    // YOUTUBE_VIDEO_URL comment for why that stays true rather than adding a real pattern for
    // it) - so a more specific YouTube-module match, when one is registered, is surfaced here as
    // an addition on top of the generic URL matches rather than instead of them.
    const youtubeMatches = iocType === IOC_TYPES.URL && isYoutubeVideoUrl(input)
      ? rankToolsForValue(IOC_TYPES.YOUTUBE_VIDEO_URL, context.registry)
      : [];
    const orderedMatches = youtubeMatches.length > 0
      ? [...youtubeMatches, ...matches.filter((entry) => !youtubeMatches.includes(entry))]
      : matches;
    return { kind: 'value', value: input, iocType, matches: orderedMatches };
  }

  const pivot = parsePivot(input, context);
  if (pivot) return pivot;

  const matches = matchTools(input, context.registry);
  if (matches.length > 0) return { kind: 'text', query: input, matches };

  const fallbackMatches = rankIdentityFallback(input, context.registry);
  if (fallbackMatches.length > 0) return { kind: 'fallback', value: input, matches: fallbackMatches };

  return { kind: 'text', query: input, matches: [] };
}

/**
 * Shared grammar layer consumed by both palette hosts (the modal CommandPalette and the `/`
 * StartScreen page) — everything about *what a given input means* lives here so it's defined
 * once; what each host actually *does* about it (navigate+close+breadcrumb vs. plain navigate)
 * stays with the host. See docs/adr/ note on the StartScreen/CommandPalette split for why the
 * two hosts exist at all rather than being collapsed into one.
 */

export interface Recent {
  toolId: string;
  [key: string]: unknown;
}

/**
 * Merges pinned tools, recently-used tools, and the full registry into the empty-query result
 * list, deduped by entry id (pinned first, then recent, then the rest of the registry).
 */
export function mergeEmptyStateResults({ pinnedIds, recents, registry }: {
  pinnedIds: string[];
  recents: Recent[];
  registry: RegistryEntry[];
}): SelectableResult[] {
  const pinnedEntries = pinnedIds.map((id) => registry.find((e) => e.id === id)).filter((e): e is RegistryEntry => Boolean(e));
  const recentEntries = recents.map((r) => registry.find((e) => e.id === r.toolId)).filter((e): e is RegistryEntry => Boolean(e));
  const seen = new Set<string>();
  return [...pinnedEntries, ...recentEntries, ...registry]
    .filter((entry) => (seen.has(entry.id) ? false : seen.add(entry.id)))
    .map((entry) => ({ type: 'entry' as const, entry }));
}

export interface BannerDescriptor {
  severity: 'info' | 'warning';
  i18nKey: string;
  params: Record<string, unknown>;
}

/**
 * Plain data (not JSX) describing the informational banner for a parsed query, so each host can
 * render it with its own Alert styling/spacing via its own i18n `t()`. Returns null when the
 * current `parsed.kind` has no banner.
 */
export function getBannerDescriptor(parsed: ParsedQuery): BannerDescriptor | null {
  if (parsed.kind === 'value') {
    return { severity: 'info', i18nKey: 'banners.detectedType', params: { type: parsed.iocType, value: parsed.value } };
  }
  if (parsed.kind === 'pivot') {
    return { severity: 'info', i18nKey: 'banners.pivot', params: { value: parsed.value, tool: parsed.tool.label } };
  }
  if (parsed.kind === 'fallback') {
    return { severity: 'info', i18nKey: 'banners.fallback', params: { value: parsed.value } };
  }
  if (parsed.kind === 'instant') {
    return { severity: 'info', i18nKey: 'banners.instant', params: { op: parsed.op, value: parsed.value } };
  }
  if (parsed.kind === 'action' && parsed.action === 'unknown') {
    return { severity: 'warning', i18nKey: 'banners.unknownAction', params: { raw: parsed.raw } };
  }
  return null;
}

export type SelectionDecision =
  | { type: 'complete-suggestion'; operator: WhichKeyOperator; suggestion: string }
  | { type: 'instant'; op: string; value: string }
  | { type: 'action'; action: ActionParsed }
  | { type: 'open'; entry: RegistryEntry; value: string | null }
  | null;

/**
 * Decides what selecting (click, Enter, digit-jump) row `index` of `visibleResults` means for
 * the current `parsed` query — a plain decision object, not an effect. `visibleResults` must be
 * the actually-displayed list (i.e. `mergeEmptyStateResults`'s output for `kind: 'empty'`, not
 * just `getSelectableResults(parsed)`) so an empty-state pinned/recent row resolves to `open`
 * like every other entry row, instead of falling through unhandled.
 */
export function resolveSelection(parsed: ParsedQuery, visibleResults: SelectableResult[], index: number): SelectionDecision {
  if (parsed.kind === 'which-key') {
    const row = visibleResults[index];
    const suggestion = row?.type === 'suggestion' ? row.value : undefined;
    return suggestion ? { type: 'complete-suggestion', operator: parsed.operator, suggestion } : null;
  }
  if (parsed.kind === 'instant') {
    return { type: 'instant', op: parsed.op, value: parsed.value };
  }
  if (parsed.kind === 'action') {
    return { type: 'action', action: parsed };
  }
  if (parsed.kind === 'pivot') {
    const row = visibleResults[index];
    const entry = (row?.type === 'entry' ? row.entry : undefined) ?? parsed.tool;
    return { type: 'open', entry, value: parsed.value };
  }
  if (parsed.kind === 'value' || parsed.kind === 'fallback') {
    const row = visibleResults[index];
    const entry = row?.type === 'entry' ? row.entry : undefined;
    return entry ? { type: 'open', entry, value: parsed.value } : null;
  }
  // 'empty' rows are always { type: 'entry' }, same shape as 'text'/'tag'/'type' matches - none
  // of these kinds carry a typed value, so the opened entry gets none either.
  const row = visibleResults[index];
  const entry = row?.type === 'entry' ? row.entry : undefined;
  return entry ? { type: 'open', entry, value: null } : null;
}

/** Turns a `resolveSelection` decision into a call against the host's own effect functions. */
export function createGrammarDispatch({ onQueryChange, onInstantAnswer, onAction, onOpenEntry }: {
  onQueryChange: (query: string) => void;
  onInstantAnswer: (op: string, value: string) => void;
  onAction: (action: ActionParsed) => void;
  onOpenEntry: (entry: RegistryEntry, value: string | null) => void;
}) {
  return (decision: SelectionDecision) => {
    if (!decision) return;
    if (decision.type === 'complete-suggestion') {
      onQueryChange(`${decision.operator}${decision.suggestion}`);
      return;
    }
    if (decision.type === 'instant') { onInstantAnswer(decision.op, decision.value); return; }
    if (decision.type === 'action') { onAction(decision.action); return; }
    if (decision.type === 'open') { onOpenEntry(decision.entry, decision.value); }
  };
}

/**
 * The keyboard subset common to both palette hosts: bounded arrow-key navigation, Tab-completes
 * the top which-key suggestion, Enter/digit-jump resolve+dispatch a selection. Returns whether it
 * handled the event, so a host can layer its own extra shortcuts (history cycling, action panel,
 * copy, ...) on top by checking this first. Escape is deliberately excluded - closing vs. merely
 * clearing the query is host UI lifecycle, not grammar.
 */
export function handleGrammarNavKey(event: KeyboardEvent, { parsed, visibleResults, selectedIndex, setSelectedIndex, dispatch }: {
  parsed: ParsedQuery;
  visibleResults: SelectableResult[] | null | undefined;
  selectedIndex: number;
  setSelectedIndex: (updater: (prev: number) => number) => void;
  dispatch: (decision: SelectionDecision) => void;
}): boolean {
  const results = visibleResults ?? [];

  if (event.key === 'ArrowDown') {
    event.preventDefault();
    setSelectedIndex((prev) => Math.min(prev + 1, Math.max(results.length - 1, 0)));
    return true;
  }
  if (event.key === 'ArrowUp') {
    event.preventDefault();
    setSelectedIndex((prev) => Math.max(prev - 1, 0));
    return true;
  }
  if (event.key === 'Enter') {
    event.preventDefault();
    dispatch(resolveSelection(parsed, results, selectedIndex));
    return true;
  }
  if (event.key === 'Tab' && parsed.kind === 'which-key' && results.length > 0) {
    event.preventDefault();
    dispatch(resolveSelection(parsed, results, 0));
    return true;
  }
  // Requires Cmd/Ctrl - a bare digit must stay a plain character, since typed values (IPs,
  // ports, hashes, CVE years) are full of digits and would otherwise never reach the input.
  if ((event.metaKey || event.ctrlKey) && event.key >= '1' && event.key <= '9') {
    const index = Number(event.key) - 1;
    if (index < results.length) {
      event.preventDefault();
      dispatch(resolveSelection(parsed, results, index));
      return true;
    }
  }
  return false;
}
