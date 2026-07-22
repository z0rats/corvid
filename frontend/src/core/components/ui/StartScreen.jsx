import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import useMediaQuery from '@mui/material/useMediaQuery';
import { alpha, useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import InputBase from '@mui/material/InputBase';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import { useAtomValue } from 'jotai';
import SearchIcon from '@mui/icons-material/SearchOutlined';
import { generalSettingsState } from '../../state/atoms';
import { buildCommandRegistry, resolveEntryPath } from '../../config/commandRegistry';
import { parseQuery, VALUE_KINDS } from '../../utils/commandParser';
import { detectIocType } from '../../utils/iocTypeDetection';
import { buildPrefillUrl } from '../../utils/crossFeatureNav';
import { copyToClipboard } from '../../utils/clipboard';
import { addRecent, addQueryToHistory, getPinnedToolIds, getRecents } from '../../utils/commandPaletteStorage';
import { getSelectableResults, OPEN_COMMAND_PALETTE_EVENT } from '../../hooks/useCommandPalette';
import { useThemeManager } from '../../hooks/ui/useThemeManager';
import api from '../../services/baseApi';
import ResultList from './CommandPalette/ResultList';
import TileGrid from './CommandPalette/TileGrid';

// Illustrative example queries — literal grammar tokens (see commandParser.js), not translated
// prose, same reasoning as BUILTIN_ACTIONS/type: aliases staying English in both locales.
const EXAMPLE_CHIPS = [
  { label: 'reddit', query: 'reddit' },
  { label: '185.220.101.7', query: '185.220.101.7' },
  { label: '0x1f98…f984 (ETH)', query: '0x1f98431c8ad98523631ae4a59f267346ea31f984' },
  { label: 'defang 185.220.101.7', query: 'defang 185.220.101.7' },
  { label: '#recon', query: '#recon' },
  { label: 'type:hash', query: 'type:hash' },
  { label: '>settings', query: '>settings' },
];
const EXAMPLE_PIVOT_CHIP = { label: 'john_doe reddit', query: 'john_doe reddit' };

/**
 * `/` home screen — the search bar re-rendered as a page instead of a modal overlay (see
 * docs/command-palette-plan.md's "doubles as the app's home screen" principle). Deliberately a
 * lighter subset of the palette's grammar: tool search, recognized-value ranking, #tag/type:kind
 * filters, `defang`/`fang` instant answers, and the `>settings`/`>theme` actions all run here
 * directly. The action panel and the record/playbook flows stay modal-only — Enter on those
 * hands off to the full palette (`OPEN_COMMAND_PALETTE_EVENT`, carrying the typed query along)
 * rather than silently doing nothing, reachable any time via `/` or Cmd/Ctrl+K regardless.
 */
export default function StartScreen() {
  const { t } = useTranslation('commandPalette');
  // sidebarConfig.jsx's i18nKeys (nav.*) live in the default 'common' namespace.
  const { t: tCommon } = useTranslation();
  const navigate = useNavigate();
  const theme = useTheme();
  const { toggleColorMode } = useThemeManager();
  const generalSettings = useAtomValue(generalSettingsState);
  const isCoarsePointer = useMediaQuery('(pointer: coarse)');
  const showTiles = (generalSettings?.always_tiles ?? false) || isCoarsePointer;

  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [notice, setNotice] = useState(null); // { message, severity }
  const inputRef = useRef(null);

  useEffect(() => {
    // autoFocus alone races with the very first keystroke in some environments (jsdom included)
    // — same fix as CommandPalette.jsx's own input.
    const id = requestAnimationFrame(() => inputRef.current?.focus());
    return () => cancelAnimationFrame(id);
  }, []);

  const registry = useMemo(() => buildCommandRegistry(tCommon), [tCommon]);
  const parsed = useMemo(() => parseQuery(query, { registry }), [query, registry]);
  const results = useMemo(() => getSelectableResults(parsed), [parsed]);

  const emptyStateResults = useMemo(() => {
    if (parsed.kind !== 'empty') return null;
    const pinnedEntries = getPinnedToolIds().map((id) => registry.find((e) => e.id === id)).filter(Boolean);
    const recentEntries = getRecents().map((r) => registry.find((e) => e.id === r.toolId)).filter(Boolean);
    const seen = new Set();
    return [...pinnedEntries, ...recentEntries, ...registry]
      .filter((entry) => (seen.has(entry.id) ? false : seen.add(entry.id)))
      .map((entry) => ({ type: 'entry', entry }));
  }, [parsed.kind, registry]);

  const visibleResults = parsed.kind === 'empty' ? emptyStateResults : results;

  const recentNames = useMemo(
    () => getRecents().map((r) => registry.find((e) => e.id === r.toolId)?.label).filter(Boolean).slice(0, 3),
    [registry],
  );

  const openEntry = (entry, value) => {
    const iocType = value ? detectIocType(value) : undefined;
    const path = resolveEntryPath(entry, iocType);
    navigate(value ? buildPrefillUrl(path, value) : path);
    addRecent({ type: 'tool', toolId: entry.id, value: value || undefined });
    if (query.trim()) addQueryToHistory(query);
  };

  const fillExample = (exampleQuery) => {
    setQuery(exampleQuery);
    setSelectedIndex(0);
    inputRef.current?.focus();
  };

  const completeWhichKey = (index) => {
    const suggestion = visibleResults[index]?.value;
    if (!suggestion) return;
    const trimmed = query.trim();
    const operator = trimmed[0] === '#' ? '#' : (trimmed.toLowerCase().startsWith('type:') ? 'type:' : '>');
    setQuery(operator === '#' ? `#${suggestion}` : operator === 'type:' ? `type:${suggestion}` : `>${suggestion}`);
  };

  const runInstantAnswer = async (op, value) => {
    try {
      const response = await api.post('/api/defang/', { text: value, operation: op });
      const processed = response.data?.results?.[0]?.processed ?? value;
      const copied = await copyToClipboard(processed);
      if (query.trim()) addQueryToHistory(query);
      setNotice({
        message: copied ? t('notices.copied', { value: processed }) : processed,
        severity: copied ? 'success' : 'info',
      });
    } catch {
      setNotice({ message: t('notices.instantAnswerFailed'), severity: 'error' });
    }
    setQuery('');
  };

  const runAction = (parsedAction) => {
    if (parsedAction.action === 'settings') { navigate('/settings'); setQuery(''); return; }
    if (parsedAction.action === 'theme') { toggleColorMode(); setQuery(''); return; }
    if (parsedAction.action === 'unknown') return; // banner already explains it; nothing to run
    // record-start / record-stop / playbook-manage / playbook-run stay modal-only (recording
    // banner, inline name prompt, playbook list) — hand off to the full palette instead of
    // silently doing nothing, carrying the typed query so it doesn't need retyping.
    window.dispatchEvent(new CustomEvent(OPEN_COMMAND_PALETTE_EVENT, { detail: { query } }));
    setQuery('');
  };

  const handleSelect = (index) => {
    const item = visibleResults[index];
    if (!item) return;
    if (item.type === 'entry') {
      const value = VALUE_KINDS.includes(parsed.kind) ? parsed.value : null;
      openEntry(item.entry, value);
      return;
    }
    if (item.type === 'suggestion') completeWhichKey(index);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Escape') {
      setQuery('');
      setSelectedIndex(0);
      return;
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, Math.max((visibleResults?.length ?? 1) - 1, 0)));
      return;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, 0));
      return;
    }
    if (event.key === 'Enter') {
      event.preventDefault();
      if (parsed.kind === 'instant') { runInstantAnswer(parsed.op, parsed.value); return; }
      if (parsed.kind === 'action') { runAction(parsed); return; }
      handleSelect(selectedIndex);
      return;
    }
    if (event.key === 'Tab' && parsed.kind === 'which-key' && visibleResults?.length > 0) {
      event.preventDefault();
      completeWhichKey(0);
      return;
    }
    // Requires Cmd/Ctrl — a bare digit must stay a plain character, since typed values (IPs,
    // ports, hashes, CVE years) are full of digits and would otherwise never reach the input.
    if ((event.metaKey || event.ctrlKey) && event.key >= '1' && event.key <= '9') {
      const index = Number(event.key) - 1;
      if (visibleResults && index < visibleResults.length) {
        event.preventDefault();
        handleSelect(index);
      }
    }
  };

  const renderBanner = () => {
    if (parsed.kind === 'value') {
      return (
        <Alert severity="info" variant="outlined" sx={{ mt: 2 }}>
          {t('banners.detectedType', { type: parsed.iocType, value: parsed.value })}
        </Alert>
      );
    }
    if (parsed.kind === 'pivot') {
      return (
        <Alert severity="info" variant="outlined" sx={{ mt: 2 }}>
          {t('banners.pivot', { value: parsed.value, tool: parsed.tool.label })}
        </Alert>
      );
    }
    if (parsed.kind === 'fallback') {
      return (
        <Alert severity="info" variant="outlined" sx={{ mt: 2 }}>
          {t('banners.fallback', { value: parsed.value })}
        </Alert>
      );
    }
    if (parsed.kind === 'instant') {
      return (
        <Alert severity="info" variant="outlined" sx={{ mt: 2 }}>
          {t('banners.instant', { op: parsed.op, value: parsed.value })}
        </Alert>
      );
    }
    if (parsed.kind === 'action' && parsed.action === 'unknown') {
      return (
        <Alert severity="warning" variant="outlined" sx={{ mt: 2 }}>
          {t('banners.unknownAction', { raw: parsed.raw })}
        </Alert>
      );
    }
    return null;
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 120px)' }}>
      <Paper
        variant="outlined"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 2,
          p: { xs: 2, sm: 3 },
          bgcolor: 'background.paper',
        }}
        onKeyDown={handleKeyDown}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography
            variant="caption"
            sx={{
              fontFamily: '"JetBrains Mono", monospace',
              letterSpacing: '0.1em',
              color: 'text.secondary',
              textTransform: 'uppercase',
            }}
          >
            {t('startScreen.brand')}
          </Typography>
          <Typography
            variant="caption"
            sx={{ fontFamily: '"JetBrains Mono", monospace', color: 'text.secondary' }}
          >
            {t('startScreen.focusHint')}
          </Typography>
        </Box>

        <Divider sx={{ mt: 1.5, mb: { xs: 3, sm: 5 } }} />

        <Box sx={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          gap: 2, width: '100%', maxWidth: 640, mx: 'auto',
        }}
        >
          {query === '' && (
            <Stack direction="row" spacing={1} rowGap={1} flexWrap="wrap" justifyContent="center">
              {EXAMPLE_CHIPS.map((chip) => (
                <Chip
                  key={chip.label}
                  label={chip.label}
                  variant="outlined"
                  onClick={() => fillExample(chip.query)}
                  sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem' }}
                />
              ))}
            </Stack>
          )}

          {query === '' && (
            <Chip
              label={EXAMPLE_PIVOT_CHIP.label}
              variant="outlined"
              onClick={() => fillExample(EXAMPLE_PIVOT_CHIP.query)}
              sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem' }}
            />
          )}

          <Box
            sx={{
              display: 'flex', alignItems: 'center', gap: 1, width: '100%',
              px: 2, py: 1.5, borderRadius: 2,
              border: `1px solid ${theme.palette.divider}`,
              bgcolor: alpha(theme.palette.text.primary, 0.03),
            }}
          >
            <SearchIcon color="action" />
            <InputBase
              inputRef={inputRef}
              fullWidth
              autoFocus
              placeholder={t('searchPlaceholder')}
              value={query}
              onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
              inputProps={{ 'aria-label': t('searchPlaceholder') }}
              sx={{ fontFamily: '"JetBrains Mono", monospace' }}
            />
          </Box>

          <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center' }}>
            {t('startScreen.pasteHint')}
          </Typography>

          {renderBanner()}

          {query === '' && recentNames.length > 0 && (
            <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center' }}>
              {t('startScreen.recentHint', { items: recentNames.join(', ') })}
            </Typography>
          )}
        </Box>

        <Box sx={{ mt: 3, width: '100%', maxWidth: 640, mx: 'auto' }}>
          {['instant', 'action'].includes(parsed.kind) ? (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', py: 2 }}>
              {t('footer.hint')}
            </Typography>
          ) : showTiles ? (
            <TileGrid
              registry={(visibleResults ?? []).map((r) => r.entry).filter(Boolean)}
              onOpen={(entry) => openEntry(entry, parsed.value ?? null)}
            />
          ) : (
            <ResultList
              results={visibleResults ?? []}
              selectedIndex={selectedIndex}
              onSelect={handleSelect}
              onActionPanel={() => {}}
            />
          )}
        </Box>
      </Paper>

      <Snackbar
        open={Boolean(notice)}
        autoHideDuration={4000}
        onClose={() => setNotice(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        {notice && (
          <Alert severity={notice.severity} onClose={() => setNotice(null)}>
            {notice.message}
          </Alert>
        )}
      </Snackbar>
    </Box>
  );
}
