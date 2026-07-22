import { useMemo, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Modal from '@mui/material/Modal';
import Fade from '@mui/material/Fade';
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import InputBase from '@mui/material/InputBase';
import Typography from '@mui/material/Typography';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import Divider from '@mui/material/Divider';
import SearchIcon from '@mui/icons-material/SearchOutlined';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useCommandPalette } from '../../../hooks/useCommandPalette';
import { VALUE_KINDS } from '../../../utils/commandParser';
import ResultList from './ResultList';
import ActionPanel from './ActionPanel';
import Breadcrumbs from './Breadcrumbs';
import RecordingBanner from './RecordingBanner';
import ShortcutSheet from './ShortcutSheet';
import TileGrid from './TileGrid';
import PlaybookManage from './PlaybookManage';

/**
 * The command palette overlay. Must be mounted inside the AccessGate subtree (Layout.jsx),
 * never beside AccessGate in App.jsx, or the `/`-listener in useCommandPalette would fire on
 * the pre-auth token screen — see docs/command-palette-plan.md's mount-point requirement.
 */
export default function CommandPalette() {
  const { t } = useTranslation('commandPalette');
  const palette = useCommandPalette();
  const inputRef = useRef(null);
  const paperRef = useRef(null);
  const isCoarsePointer = useMediaQuery('(pointer: coarse)');
  const showTiles = palette.alwaysTiles || isCoarsePointer;

  useEffect(() => {
    if (palette.isOpen) {
      // Modal's own focus-trap moves focus into the container first; grab the input right after.
      const id = requestAnimationFrame(() => inputRef.current?.focus());
      return () => cancelAnimationFrame(id);
    }
    return undefined;
  }, [palette.isOpen]);

  const emptyStateResults = useMemo(() => {
    if (palette.parsed.kind !== 'empty') return null;
    const recentEntries = palette.recents
      .map((r) => palette.registry.find((e) => e.id === r.toolId))
      .filter(Boolean);
    const pinnedEntries = palette.pinnedIds
      .map((id) => palette.registry.find((e) => e.id === id))
      .filter(Boolean);
    const seen = new Set();
    const merged = [...pinnedEntries, ...recentEntries, ...palette.registry].filter((entry) => {
      if (seen.has(entry.id)) return false;
      seen.add(entry.id);
      return true;
    });
    return merged.map((entry) => ({ type: 'entry', entry }));
  }, [palette.parsed.kind, palette.recents, palette.pinnedIds, palette.registry]);

  const visibleResults = palette.parsed.kind === 'empty' ? emptyStateResults : palette.results;

  const actionPanelEntry = palette.actionPanelIndex !== null
    ? visibleResults?.[palette.actionPanelIndex]?.entry
    : null;
  const actionPanelValue = VALUE_KINDS.includes(palette.parsed.kind) ? palette.parsed.value : null;

  const handleSelect = (index) => {
    palette.setSelectedIndex(index);
    palette.runSelected(index);
  };

  const renderBanner = () => {
    if (palette.parsed.kind === 'value') {
      return (
        <Alert severity="info" variant="outlined" sx={{ mx: 2, mt: 1 }}>
          {t('banners.detectedType', { type: palette.parsed.iocType, value: palette.parsed.value })}
        </Alert>
      );
    }
    if (palette.parsed.kind === 'pivot') {
      return (
        <Alert severity="info" variant="outlined" sx={{ mx: 2, mt: 1 }}>
          {t('banners.pivot', { value: palette.parsed.value, tool: palette.parsed.tool.label })}
        </Alert>
      );
    }
    if (palette.parsed.kind === 'fallback') {
      return (
        <Alert severity="info" variant="outlined" sx={{ mx: 2, mt: 1 }}>
          {t('banners.fallback', { value: palette.parsed.value })}
        </Alert>
      );
    }
    if (palette.parsed.kind === 'instant') {
      return (
        <Alert severity="info" variant="outlined" sx={{ mx: 2, mt: 1 }}>
          {t('banners.instant', { op: palette.parsed.op, value: palette.parsed.value })}
        </Alert>
      );
    }
    if (palette.parsed.kind === 'action' && palette.parsed.action === 'unknown') {
      return (
        <Alert severity="warning" variant="outlined" sx={{ mx: 2, mt: 1 }}>
          {t('banners.unknownAction', { raw: palette.parsed.raw })}
        </Alert>
      );
    }
    return null;
  };

  return (
    <>
      <Modal
        open={palette.isOpen}
        onClose={(event, reason) => {
          // Escape is deliberately handled by handlePaletteKeyDown below instead (clear the
          // query first, close on a second press) — MUI's Modal otherwise closes unconditionally
          // on any Escape regardless of disableEscapeKeyDown, which would skip that first stage.
          if (reason !== 'escapeKeyDown') palette.close();
        }}
      >
        <Fade in={palette.isOpen}>
          <Paper
            ref={paperRef}
            elevation={8}
            sx={{
              position: 'absolute', top: '12%', left: '50%', transform: 'translateX(-50%)',
              width: { xs: '92%', sm: 560 }, maxWidth: '95vw', borderRadius: 2, overflow: 'hidden',
            }}
            onKeyDown={palette.handlePaletteKeyDown}
          >
            {palette.isRecording && (
              <RecordingBanner
                stepCount={palette.recordingSteps.length}
                onStop={() => palette.runAction({ kind: 'action', action: 'record-stop', name: null })}
              />
            )}

            <Box sx={{ display: 'flex', alignItems: 'center', px: 2, py: 1.5, gap: 1 }}>
              <SearchIcon color="action" />
              <InputBase
                inputRef={inputRef}
                fullWidth
                autoFocus
                placeholder={t('searchPlaceholder')}
                value={palette.query}
                onChange={(e) => palette.setQuery(e.target.value)}
                inputProps={{ 'aria-label': t('searchPlaceholder') }}
              />
            </Box>

            {palette.pendingRecordStopName && (
              <Box sx={{ display: 'flex', gap: 1, px: 2, pb: 1.5 }}>
                <TextField
                  size="small"
                  fullWidth
                  autoFocus
                  placeholder={t('recording.namePlaceholder')}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') { palette.finishRecording(e.target.value.trim()); palette.close(); }
                  }}
                />
                <Button size="small" onClick={palette.cancelRecordStopPrompt}>{t('recording.cancel')}</Button>
              </Box>
            )}

            <Divider />
            {renderBanner()}
            <Breadcrumbs trail={palette.breadcrumbs} />

            {palette.view === 'playbook-manage' ? (
              <PlaybookManage
                playbooks={palette.playbooks}
                registry={palette.registry}
                onRename={palette.renamePlaybook}
                onDelete={palette.deletePlaybook}
                onRunNow={(name, value) => { palette.runPlaybookNow(name, value); palette.close(); }}
                onBack={() => palette.setView('search')}
              />
            ) : showTiles ? (
              <TileGrid
                registry={(visibleResults ?? []).map((r) => r.entry).filter(Boolean)}
                onOpen={(entry) => palette.openEntry(entry, palette.parsed.value ?? null)}
              />
            ) : (
              <ResultList
                results={visibleResults ?? []}
                selectedIndex={palette.selectedIndex}
                onSelect={handleSelect}
                onActionPanel={(index) => {
                  palette.setSelectedIndex(index);
                  palette.toggleActionPanel(index);
                }}
              />
            )}

            <Box sx={{ px: 2, py: 0.75, display: 'flex', justifyContent: 'space-between', bgcolor: 'action.hover' }}>
              <Typography variant="caption" color="text.secondary">{t('footer.hint')}</Typography>
              <Typography
                variant="caption"
                color="primary"
                sx={{ cursor: 'pointer' }}
                onClick={palette.openShortcutSheet}
              >
                {t('footer.shortcuts')}
              </Typography>
            </Box>
          </Paper>
        </Fade>
      </Modal>

      <ActionPanel
        anchorEl={palette.actionPanelIndex !== null ? paperRef.current : null}
        entry={actionPanelEntry}
        value={actionPanelValue}
        pinnedIds={palette.pinnedIds}
        onClose={palette.closeActionPanel}
        onOpen={() => actionPanelEntry && palette.openEntry(actionPanelEntry, actionPanelValue)}
        onTogglePin={() => actionPanelEntry && palette.togglePin(actionPanelEntry.id)}
        onCopy={() => palette.copyFocusedValue?.(false)}
        onCopyDefanged={() => palette.copyFocusedValue?.(true)}
        onAddToBulk={() => palette.addFocusedValueToBulk?.()}
      />

      <ShortcutSheet open={palette.showShortcutSheet} onClose={palette.closeShortcutSheet} />

      <Snackbar
        open={Boolean(palette.notice)}
        autoHideDuration={4000}
        onClose={palette.dismissNotice}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        {palette.notice && (
          <Alert severity={palette.notice.severity} onClose={palette.dismissNotice}>
            {palette.notice.message}
          </Alert>
        )}
      </Snackbar>
    </>
  );
}
