import { useState, useCallback, useMemo, useRef } from 'react';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import { generalSettingsState } from '../state/atoms';
import { useThemeManager } from './ui/useThemeManager';
import api from '../services/baseApi';
import { useGlobalPaletteShortcuts } from './useGlobalPaletteShortcuts';
import { usePlaybooks } from './usePlaybooks';
import { buildCommandRegistry, resolveEntryPath } from '../config/commandRegistry';
import {
  parseQuery, VALUE_KINDS, getSelectableResults,
  mergeEmptyStateResults, resolveSelection, createGrammarDispatch, handleGrammarNavKey,
} from '../utils/commandParser';
import { detectIocType } from '../utils/iocTypeDetection';
import { copyToClipboard } from '../utils/clipboard';
import { buildPrefillUrl } from '../utils/crossFeatureNav';
import {
  getPinnedToolIds, togglePinnedToolId,
  getRecents, addRecent,
  getQueryHistory, addQueryToHistory,
} from '../utils/commandPaletteStorage';

async function defangOrFang(value, op) {
  const response = await api.post('/api/defang/', { text: value, operation: op });
  return response.data?.results?.[0]?.processed ?? value;
}

export function useCommandPalette() {
  const { t } = useTranslation('commandPalette');
  // sidebarConfig.jsx's i18nKeys (nav.*) live in the default 'common' namespace, not
  // 'commandPalette' — buildCommandRegistry needs this one, not the palette's own copy above.
  const { t: tCommon } = useTranslation();
  const navigate = useNavigate();
  const { toggleColorMode } = useThemeManager();
  const generalSettings = useAtomValue(generalSettingsState);

  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [actionPanelIndex, setActionPanelIndex] = useState(null);
  const [showShortcutSheet, setShowShortcutSheet] = useState(false);
  const [view, setView] = useState('search'); // 'search' | 'playbook-manage'
  const [notice, setNotice] = useState(null); // { message, severity }

  const [breadcrumbs, setBreadcrumbs] = useState([]);
  const [pinnedIds, setPinnedIds] = useState(getPinnedToolIds);
  const [recents, setRecents] = useState(getRecents);
  const historyPointer = useRef(-1);

  const registry = useMemo(() => buildCommandRegistry(tCommon), [tCommon]);

  const showNotice = useCallback((message, severity = 'success') => {
    setNotice({ message, severity });
  }, []);

  const resetTransientState = useCallback(() => {
    setQuery('');
    setSelectedIndex(0);
    setActionPanelIndex(null);
    setView('search');
    historyPointer.current = -1;
  }, []);

  const open = useCallback((initialQuery = '') => {
    setQuery(initialQuery);
    setIsOpen(true);
    setSelectedIndex(0);
    setActionPanelIndex(null);
    setView('search');
    historyPointer.current = -1;
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    resetTransientState();
  }, [resetTransientState]);

  useGlobalPaletteShortcuts(isOpen, open, close, () => setShowShortcutSheet(true));

  // The non-recording-aware open path — everything but feeding an active recording session.
  // Handed to usePlaybooks as onOpenEntry (see its docstring); everywhere else uses the
  // recording-aware `openEntry` below.
  const openEntryRaw = useCallback((entry, value) => {
    const iocType = value ? detectIocType(value) : undefined;
    const path = resolveEntryPath(entry, iocType);
    navigate(value ? buildPrefillUrl(path, value) : path);

    setRecents(addRecent({ type: 'tool', toolId: entry.id, value: value || undefined }));
    if (query.trim()) addQueryToHistory(query);
    setBreadcrumbs((prev) => [...prev, { label: entry.label, toolId: entry.id, value }]);

    close();
  }, [navigate, query, close]);

  const playbookApi = usePlaybooks(registry, {
    onOpenEntry: openEntryRaw,
    setBreadcrumbs,
    showNotice,
  });

  const openEntry = useCallback((entry, value) => {
    openEntryRaw(entry, value);
    if (playbookApi.isRecording) playbookApi.recordStep(entry.id);
    // Deps list the specific fields used, not `playbookApi` itself — usePlaybooks returns a new
    // object every render, so depending on the whole object would recreate this (and everything
    // downstream of it) on every render regardless of whether recording state actually changed.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [openEntryRaw, playbookApi.isRecording, playbookApi.recordStep]);

  const parsed = useMemo(
    () => parseQuery(query, { registry, playbooks: playbookApi.playbooks, isRecording: playbookApi.isRecording }),
    [query, registry, playbookApi.playbooks, playbookApi.isRecording],
  );

  const results = useMemo(() => getSelectableResults(parsed), [parsed]);

  // The actually-displayed list: for an empty query this is the pinned/recent/registry merge,
  // not `results` (which `getSelectableResults` leaves empty for `kind: 'empty'`). Computed here
  // rather than in CommandPalette.jsx so `runSelected`/`handlePaletteKeyDown` below resolve
  // against the same rows the user sees - selecting a pinned/recent row used to silently no-op
  // in the list view (only the tile-grid view opened it, via its own direct `openEntry` call).
  const visibleResults = useMemo(
    () => (parsed.kind === 'empty' ? mergeEmptyStateResults({ pinnedIds, recents, registry }) : results),
    [parsed.kind, pinnedIds, recents, registry, results],
  );

  const runInstantAnswer = useCallback(async (op, value) => {
    try {
      const processed = await defangOrFang(value, op);
      const copied = await copyToClipboard(processed);
      addQueryToHistory(query);
      showNotice(copied ? t('notices.copied', { value: processed }) : processed, copied ? 'success' : 'info');
    } catch {
      showNotice(t('notices.instantAnswerFailed'), 'error');
    }
    close();
  }, [query, showNotice, t, close]);

  const runAction = useCallback((parsedAction) => {
    switch (parsedAction.action) {
      case 'settings':
        navigate('/settings');
        close();
        break;
      case 'theme':
        toggleColorMode();
        close();
        break;
      case 'record-start':
        playbookApi.startRecording();
        setQuery('');
        showNotice(t('notices.recordingStarted'));
        break;
      case 'record-stop':
        if (parsedAction.name) {
          playbookApi.finishRecording(parsedAction.name);
          close();
        } else {
          playbookApi.requestRecordStopName();
        }
        break;
      case 'playbook-manage':
        setView('playbook-manage');
        break;
      case 'playbook-run':
        playbookApi.runPlaybook(parsedAction.playbookName, parsedAction.value);
        break;
      default:
        showNotice(t('notices.unknownAction'), 'info');
    }
    // See openEntry above re: depending on individual playbookApi fields instead of the object.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    navigate, close, toggleColorMode, showNotice, t,
    playbookApi.startRecording, playbookApi.finishRecording,
    playbookApi.requestRecordStopName, playbookApi.runPlaybook,
  ]);

  const dispatch = useMemo(() => createGrammarDispatch({
    onQueryChange: setQuery,
    onInstantAnswer: runInstantAnswer,
    onAction: runAction,
    onOpenEntry: openEntry,
  }), [runInstantAnswer, runAction, openEntry]);

  const runSelected = useCallback((explicitIndex) => {
    const index = explicitIndex ?? selectedIndex;
    dispatch(resolveSelection(parsed, visibleResults, index));
  }, [dispatch, parsed, visibleResults, selectedIndex]);

  const cycleQueryHistory = useCallback((direction) => {
    const history = getQueryHistory();
    if (history.length === 0) return;
    const next = Math.min(Math.max(historyPointer.current + direction, -1), history.length - 1);
    historyPointer.current = next;
    setQuery(next === -1 ? '' : history[next]);
  }, []);

  const togglePin = useCallback((toolId) => {
    setPinnedIds(togglePinnedToolId(toolId));
  }, []);

  const copyFocusedValue = useCallback(async (defanged) => {
    const value = VALUE_KINDS.includes(parsed.kind) ? parsed.value : null;
    if (!value) return;
    const text = defanged ? await defangOrFang(value, 'defang') : value;
    const copied = await copyToClipboard(text);
    showNotice(copied ? t('notices.copied', { value: text }) : t('notices.copyFailed'), copied ? 'success' : 'error');
  }, [parsed, showNotice, t]);

  const addFocusedValueToBulk = useCallback(() => {
    const value = VALUE_KINDS.includes(parsed.kind) ? parsed.value : null;
    if (!value) return;
    navigate(buildPrefillUrl('/ioc-tools/bulk', value));
    close();
  }, [parsed, navigate, close]);

  const toggleActionPanel = useCallback((index) => {
    setActionPanelIndex((prev) => (prev === index ? null : index));
  }, []);

  // Palette-local keyboard grammar, active only while open.
  const handlePaletteKeyDown = useCallback((event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      if (query) setQuery('');
      else close();
      return;
    }
    if (handleGrammarNavKey(event, { parsed, visibleResults, selectedIndex, setSelectedIndex, dispatch })) return;
    if ((event.metaKey || event.ctrlKey) && event.key === 'ArrowUp') {
      event.preventDefault();
      cycleQueryHistory(1);
      return;
    }
    if ((event.metaKey || event.ctrlKey) && event.key === 'ArrowDown') {
      event.preventDefault();
      cycleQueryHistory(-1);
      return;
    }
    if ((event.metaKey || event.ctrlKey) && !event.shiftKey && !event.altKey && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      toggleActionPanel(selectedIndex);
      return;
    }
    if ((event.metaKey || event.ctrlKey) && event.altKey && event.key.toLowerCase() === 'c') {
      event.preventDefault();
      copyFocusedValue(true);
      return;
    }
    if ((event.metaKey || event.ctrlKey) && !event.altKey && event.key.toLowerCase() === 'c') {
      event.preventDefault();
      copyFocusedValue(false);
      return;
    }
    if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key.toLowerCase() === 'b') {
      event.preventDefault();
      addFocusedValueToBulk();
      return;
    }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'p') {
      event.preventDefault();
      const entry = visibleResults[selectedIndex]?.entry;
      if (entry) togglePin(entry.id);
    }
  }, [
    query, close, parsed, visibleResults, dispatch, cycleQueryHistory,
    toggleActionPanel, selectedIndex, copyFocusedValue, addFocusedValueToBulk, togglePin,
  ]);

  const handleQueryChange = useCallback((value) => {
    setQuery(value);
    setSelectedIndex(0);
    setActionPanelIndex(null);
  }, []);

  return {
    // state
    isOpen, query, selectedIndex, parsed, results, visibleResults, view, notice,
    isRecording: playbookApi.isRecording,
    recordingSteps: playbookApi.recordingSteps,
    pendingRecordStopName: playbookApi.pendingRecordStopName,
    breadcrumbs, pinnedIds, recents, playbooks: playbookApi.playbooks, registry,
    actionPanelIndex, showShortcutSheet,
    autoOpenOnSingleMatch: generalSettings?.auto_open_on_single_match ?? true,
    alwaysTiles: generalSettings?.always_tiles ?? false,
    // actions
    open, close, setQuery: handleQueryChange, setSelectedIndex,
    handlePaletteKeyDown, runSelected, openEntry, runInstantAnswer, runAction,
    togglePin, dismissNotice: () => setNotice(null),
    finishRecording: playbookApi.finishRecording,
    cancelRecordStopPrompt: playbookApi.cancelRecordStopPrompt,
    setView, closeShortcutSheet: () => setShowShortcutSheet(false),
    openShortcutSheet: () => setShowShortcutSheet(true),
    toggleActionPanel, closeActionPanel: () => setActionPanelIndex(null),
    copyFocusedValue, addFocusedValueToBulk,
    renamePlaybook: playbookApi.renamePlaybook,
    deletePlaybook: playbookApi.deletePlaybook,
    runPlaybookNow: playbookApi.runPlaybook,
  };
}
