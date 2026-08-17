import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
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
import {
  parseQuery, getSelectableResults,
  mergeEmptyStateResults, getBannerDescriptor, resolveSelection, createGrammarDispatch, handleGrammarNavKey,
} from '../../utils/commandParser';
import { detectIocType } from '../../utils/iocTypeDetection';
import { buildPrefillUrl } from '../../utils/crossFeatureNav';
import { copyToClipboard } from '../../utils/clipboard';
import { sha256Hex } from '../../utils/fileHash';
import { addRecent, addQueryToHistory, getPinnedToolIds, getRecents } from '../../utils/commandPaletteStorage';
import { OPEN_COMMAND_PALETTE_EVENT } from '../../hooks/useGlobalPaletteShortcuts';
import { useThemeManager } from '../../hooks/ui/useThemeManager';
import api from '../../services/baseApi';
import ResultList from './CommandPalette/ResultList';
import TileGrid from './CommandPalette/TileGrid';

// Illustrative example queries — literal grammar tokens (see commandParser.ts), not translated
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
  const [isDragOver, setIsDragOver] = useState(false);
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

  // The actually-displayed list — same grammar as the modal palette (see
  // core/hooks/useCommandPalette.ts's identical computation), just fed from a local read of
  // pinned/recents instead of hook state, since this page has no palette-open lifecycle to key
  // that state off of.
  const visibleResults = useMemo(() => {
    if (parsed.kind !== 'empty') return results;
    return mergeEmptyStateResults({ pinnedIds: getPinnedToolIds(), recents: getRecents(), registry });
  }, [parsed.kind, registry, results]);

  const recentNames = useMemo(
    () => getRecents().map((r) => registry.find((e) => e.id === r.toolId)?.label).filter(Boolean).slice(0, 3),
    [registry],
  );

  // Host-specific effects — no close()/breadcrumb/recording here, unlike the modal palette's
  // own openEntry/runInstantAnswer/runAction (core/hooks/useCommandPalette.ts): this is a page,
  // not something with an open/closed lifecycle. What each kind of parsed input *means* is
  // shared grammar (commandParser.ts); only what happens next differs per host.
  const openEntry = (entry, value) => {
    const iocType = value ? detectIocType(value) : undefined;
    const path = resolveEntryPath(entry, iocType);
    navigate(value ? buildPrefillUrl(path, value) : path);
    addRecent({ type: 'tool', toolId: entry.id, value: value || undefined });
    if (query.trim()) addQueryToHistory(query);
  };

  // Drag-and-drop counterpart to useCommandPalette.ts's global ⌘V/Ctrl+V image paste — an image
  // gets the same Image Tools hand-off, any other file is hashed client-side (no file ever
  // leaves the browser for this) and pivoted through the same SHA-256 IOC route a pasted/typed
  // hash already takes, which lands on /ioc-tools/bulk and queries VirusTotal among other
  // hash-capable services (see serviceConfig.js).
  const handleFileDrop = async (file) => {
    if (file.type.startsWith('image/')) {
      navigate('/image-tools', { state: { file } });
      return;
    }
    try {
      const hash = await sha256Hex(file);
      const iocEntry = registry.find((entry) => entry.moduleId === 'ioc_tools');
      if (iocEntry) openEntry(iocEntry, hash);
    } catch {
      setNotice({ message: t('notices.instantAnswerFailed'), severity: 'error' });
    }
  };

  const handleDragOver = (event) => {
    if (!event.dataTransfer.types.includes('Files')) return;
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (event) => {
    if (!event.dataTransfer.types.includes('Files')) return;
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file) handleFileDrop(file);
  };

  const fillExample = (exampleQuery) => {
    setQuery(exampleQuery);
    setSelectedIndex(0);
    inputRef.current?.focus();
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

  // Not memoized, unlike useCommandPalette.ts's version — openEntry/runInstantAnswer/runAction
  // here are plain closures re-created every render (not useCallback), so memoizing this against
  // a narrower dep list would risk capturing a stale one.
  const dispatch = createGrammarDispatch({
    onQueryChange: setQuery,
    onInstantAnswer: runInstantAnswer,
    onAction: runAction,
    onOpenEntry: openEntry,
  });

  const handleSelect = (index) => dispatch(resolveSelection(parsed, visibleResults, index));

  const handleKeyDown = (event) => {
    if (event.key === 'Escape') {
      setQuery('');
      setSelectedIndex(0);
      return;
    }
    handleGrammarNavKey(event, { parsed, visibleResults, selectedIndex, setSelectedIndex, dispatch });
  };

  const banner = useMemo(() => getBannerDescriptor(parsed), [parsed]);

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
          outline: isDragOver ? `2px dashed ${theme.palette.primary.main}` : 'none',
          outlineOffset: -4,
          transition: 'outline-color 0.15s ease',
        }}
        onKeyDown={handleKeyDown}
        onDragOver={handleDragOver}
        onDragEnter={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
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

          {banner && (
            <Alert severity={banner.severity} variant="outlined" sx={{ mt: 2 }}>
              {t(banner.i18nKey, banner.params)}
            </Alert>
          )}

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
