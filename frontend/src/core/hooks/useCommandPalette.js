import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import { generalSettingsState } from '../state/atoms';
import { useThemeManager } from './ui/useThemeManager';
import api from '../services/baseApi';
import { buildCommandRegistry, resolveEntryPath } from '../config/commandRegistry';
import { parseQuery, VALUE_KINDS } from '../utils/commandParser';
import { detectIocType } from '../utils/iocTypeDetection';
import { copyToClipboard } from '../utils/clipboard';
import { buildPrefillUrl } from '../utils/crossFeatureNav';
import {
  getPinnedToolIds, togglePinnedToolId,
  getRecents, addRecent,
  getQueryHistory, addQueryToHistory,
  getPlaybooks, savePlaybook, renamePlaybook, deletePlaybook,
} from '../utils/commandPaletteStorage';

// Dispatched by Layout.jsx's AppBar search-trigger button — the palette's open state is owned
// entirely inside this hook (only instantiated in CommandPalette.jsx), so opening it from
// elsewhere in the tree goes through a DOM event rather than lifting state up.
export const OPEN_COMMAND_PALETTE_EVENT = 'corvid:open-command-palette';

const EDITABLE_TAG_NAMES = new Set(['INPUT', 'TEXTAREA', 'SELECT']);

function isEditableTarget(el) {
  if (!el) return false;
  if (EDITABLE_TAG_NAMES.has(el.tagName)) return true;
  return Boolean(el.isContentEditable);
}

async function defangOrFang(value, op) {
  const response = await api.post('/api/defang/', { text: value, operation: op });
  return response.data?.results?.[0]?.processed ?? value;
}

/** Everything the currently parsed query can offer as a keyboard-selectable row. */
export function getSelectableResults(parsed) {
  if (parsed.kind === 'which-key') {
    return parsed.suggestions.map((s) => ({ type: 'suggestion', value: s }));
  }
  if (['text', 'tag', 'type', 'value', 'pivot', 'fallback'].includes(parsed.kind)) {
    return parsed.matches.map((entry) => ({ type: 'entry', entry }));
  }
  return [];
}

export function useCommandPalette() {
  const { t } = useTranslation('commandPalette');
  // sidebarConfig.jsx's i18nKeys (nav.*) live in the default 'common' namespace, not
  // 'commandPalette' — buildCommandRegistry needs this one, not the palette's own copy above.
  const { t: tCommon } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { toggleColorMode } = useThemeManager();
  const generalSettings = useAtomValue(generalSettingsState);

  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [actionPanelIndex, setActionPanelIndex] = useState(null);
  const [showShortcutSheet, setShowShortcutSheet] = useState(false);
  const [view, setView] = useState('search'); // 'search' | 'playbook-manage'
  const [notice, setNotice] = useState(null); // { message, severity }

  const [isRecording, setIsRecording] = useState(false);
  const [recordingSteps, setRecordingSteps] = useState([]);
  const [pendingRecordStopName, setPendingRecordStopName] = useState(false);

  const [breadcrumbs, setBreadcrumbs] = useState([]);
  const [pinnedIds, setPinnedIds] = useState(getPinnedToolIds);
  const [recents, setRecents] = useState(getRecents);
  const [playbooks, setPlaybooks] = useState(getPlaybooks);
  const historyPointer = useRef(-1);

  const registry = useMemo(() => buildCommandRegistry(tCommon), [tCommon]);

  const parsed = useMemo(
    () => parseQuery(query, { registry, playbooks, isRecording }),
    [query, registry, playbooks, isRecording],
  );

  const results = useMemo(() => getSelectableResults(parsed), [parsed]);

  const refreshPlaybooks = useCallback(() => setPlaybooks(getPlaybooks()), []);

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

  const recordStep = useCallback((toolId) => {
    setRecordingSteps((prev) => (prev.includes(toolId) ? prev : [...prev, toolId]));
  }, []);

  const openEntry = useCallback((entry, value) => {
    const iocType = value ? detectIocType(value) : undefined;
    const path = resolveEntryPath(entry, iocType);
    navigate(value ? buildPrefillUrl(path, value) : path);

    setRecents(addRecent({ type: 'tool', toolId: entry.id, value: value || undefined }));
    if (query.trim()) addQueryToHistory(query);
    setBreadcrumbs((prev) => [...prev, { label: entry.label, toolId: entry.id, value }]);
    if (isRecording) recordStep(entry.id);

    close();
  }, [navigate, query, isRecording, recordStep, close]);

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

  const finishRecording = useCallback((name) => {
    if (!name || recordingSteps.length === 0) {
      setIsRecording(false);
      setRecordingSteps([]);
      setPendingRecordStopName(false);
      return;
    }
    savePlaybook(name, recordingSteps);
    refreshPlaybooks();
    setIsRecording(false);
    setRecordingSteps([]);
    setPendingRecordStopName(false);
    showNotice(t('notices.playbookSaved', { name }));
  }, [recordingSteps, refreshPlaybooks, showNotice, t]);

  const runPlaybook = useCallback((playbookName, value) => {
    const playbook = playbooks.find((p) => p.name === playbookName);
    if (!playbook || playbook.steps.length === 0) {
      showNotice(t('notices.playbookNotFound', { name: playbookName }), 'error');
      return;
    }
    const [firstId, ...restIds] = playbook.steps;
    const firstEntry = registry.find((e) => e.id === firstId);
    if (!firstEntry) {
      showNotice(t('notices.playbookNotFound', { name: playbookName }), 'error');
      return;
    }
    // Only the tool IDs are recorded (see docs/command-palette-plan.md's Playbooks section) —
    // there's no generic way to capture each step's *result* value across unrelated features,
    // so replay opens step one prefilled and seeds the rest as a breadcrumb trail to continue
    // pivoting through by hand, exactly like a live chain.
    setBreadcrumbs((prev) => [
      ...prev,
      { label: firstEntry.label, toolId: firstEntry.id, value },
      ...restIds.map((id) => {
        const entry = registry.find((e) => e.id === id);
        return { label: entry?.label ?? id, toolId: id, pending: true };
      }),
    ]);
    const iocType = value ? detectIocType(value) : undefined;
    const path = resolveEntryPath(firstEntry, iocType);
    navigate(value ? buildPrefillUrl(path, value) : path);
    setRecents(addRecent({ type: 'tool', toolId: firstEntry.id, value: value || undefined }));
    close();
  }, [playbooks, registry, navigate, close, showNotice, t]);

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
        setIsRecording(true);
        setRecordingSteps([]);
        setQuery('');
        showNotice(t('notices.recordingStarted'));
        break;
      case 'record-stop':
        if (parsedAction.name) {
          finishRecording(parsedAction.name);
          close();
        } else {
          setPendingRecordStopName(true);
        }
        break;
      case 'playbook-manage':
        setView('playbook-manage');
        break;
      case 'playbook-run':
        runPlaybook(parsedAction.playbookName, parsedAction.value);
        break;
      default:
        showNotice(t('notices.unknownAction'), 'info');
    }
  }, [navigate, close, toggleColorMode, finishRecording, runPlaybook, showNotice, t]);

  const runSelected = useCallback((explicitIndex) => {
    const index = explicitIndex ?? selectedIndex;

    if (parsed.kind === 'which-key') {
      const suggestion = results[index]?.value;
      if (!suggestion) return;
      const operator = query.trim()[0] === '#' ? '#' : (query.trim().toLowerCase().startsWith('type:') ? 'type:' : '>');
      setQuery(operator === '#' ? `#${suggestion}` : operator === 'type:' ? `type:${suggestion}` : `>${suggestion}`);
      return;
    }
    if (parsed.kind === 'instant') {
      runInstantAnswer(parsed.op, parsed.value);
      return;
    }
    if (parsed.kind === 'action') {
      runAction(parsed);
      return;
    }
    if (parsed.kind === 'pivot') {
      const entry = results[index]?.entry ?? parsed.tool;
      openEntry(entry, parsed.value);
      return;
    }
    if (parsed.kind === 'value' || parsed.kind === 'fallback') {
      const entry = results[index]?.entry;
      if (entry) openEntry(entry, parsed.value);
      return;
    }
    if (['text', 'tag', 'type'].includes(parsed.kind)) {
      const entry = results[index]?.entry;
      if (entry) openEntry(entry, null);
    }
  }, [parsed, results, selectedIndex, query, openEntry, runInstantAnswer, runAction]);

  const completeTop = useCallback(() => {
    if (parsed.kind === 'which-key' && results.length > 0) {
      runSelected(0);
    }
  }, [parsed, results, runSelected]);

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

  // Global `/`, Cmd/Ctrl+K, Cmd/Ctrl+, and `?` listener — guarded against hijacking focused
  // text inputs. Cmd/Ctrl+, works regardless of open state, like every other app's preferences
  // shortcut; the rest only fire while closed to avoid fighting the palette's own key handling.
  useEffect(() => {
    const handler = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === ',') {
        event.preventDefault();
        navigate('/settings');
        if (isOpen) close();
        return;
      }
      if (isOpen) return;
      const target = event.target;
      if (event.key === '/' && !isEditableTarget(target)) {
        event.preventDefault();
        open();
        return;
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        open();
        return;
      }
      if (event.key === '?' && !isEditableTarget(target)) {
        event.preventDefault();
        setShowShortcutSheet(true);
      }
    };
    // StartScreen dispatches this with a `detail.query` payload when it hands off a
    // modal-only grammar kind (record/playbook) it deliberately doesn't implement itself —
    // Layout.jsx's own trigger dispatches a plain Event, so `detail` is undefined there.
    const handleOpenEvent = (event) => { if (!isOpen) open(event?.detail?.query ?? ''); };

    window.addEventListener('keydown', handler);
    window.addEventListener(OPEN_COMMAND_PALETTE_EVENT, handleOpenEvent);
    return () => {
      window.removeEventListener('keydown', handler);
      window.removeEventListener(OPEN_COMMAND_PALETTE_EVENT, handleOpenEvent);
    };
  }, [isOpen, open, close, navigate]);

  // Global ⌘V/Ctrl+V — a pasted image jumps to Image Tools with it preloaded, from anywhere in
  // the app (see docs/command-palette-plan.md's Keyboard shortcuts table). Image Tools' own
  // `/image-tools` page has its own local paste handler already, so this one steps aside there
  // to avoid double-handling the same clipboard event.
  useEffect(() => {
    const handlePaste = (event) => {
      if (location.pathname.startsWith('/image-tools')) return;
      const items = event.clipboardData?.items;
      if (!items) return;
      const imageItem = Array.from(items).find((item) => item.type.startsWith('image/'));
      if (!imageItem) return;
      const file = imageItem.getAsFile();
      if (!file) return;

      event.preventDefault();
      if (isOpen) close();
      navigate('/image-tools', { state: { file } });
    };
    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [location.pathname, isOpen, close, navigate]);

  // Palette-local keyboard grammar, active only while open.
  const handlePaletteKeyDown = useCallback((event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      if (query) setQuery('');
      else close();
      return;
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, Math.max(results.length - 1, 0)));
      return;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, 0));
      return;
    }
    if (event.key === 'Enter') {
      event.preventDefault();
      runSelected();
      return;
    }
    if (event.key === 'Tab') {
      event.preventDefault();
      completeTop();
      return;
    }
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
      const entry = results[selectedIndex]?.entry;
      if (entry) togglePin(entry.id);
    }
    // Requires Cmd/Ctrl — a bare digit must stay a plain character, since typed values (IPs,
    // ports, hashes, CVE years) are full of digits and would otherwise never reach the input.
    if ((event.metaKey || event.ctrlKey) && event.key >= '1' && event.key <= '9') {
      const index = Number(event.key) - 1;
      if (index < results.length) {
        event.preventDefault();
        runSelected(index);
      }
    }
  }, [
    query, close, results, runSelected, completeTop, cycleQueryHistory,
    toggleActionPanel, selectedIndex, copyFocusedValue, addFocusedValueToBulk, togglePin,
  ]);

  const handleQueryChange = useCallback((value) => {
    setQuery(value);
    setSelectedIndex(0);
    setActionPanelIndex(null);
  }, []);

  return {
    // state
    isOpen, query, selectedIndex, parsed, results, view, notice,
    isRecording, recordingSteps, pendingRecordStopName,
    breadcrumbs, pinnedIds, recents, playbooks, registry,
    actionPanelIndex, showShortcutSheet,
    autoOpenOnSingleMatch: generalSettings?.auto_open_on_single_match ?? true,
    alwaysTiles: generalSettings?.always_tiles ?? false,
    // actions
    open, close, setQuery: handleQueryChange, setSelectedIndex,
    handlePaletteKeyDown, runSelected, openEntry, runInstantAnswer, runAction,
    togglePin, dismissNotice: () => setNotice(null),
    finishRecording, cancelRecordStopPrompt: () => setPendingRecordStopName(false),
    setView, closeShortcutSheet: () => setShowShortcutSheet(false),
    openShortcutSheet: () => setShowShortcutSheet(true),
    toggleActionPanel, closeActionPanel: () => setActionPanelIndex(null),
    copyFocusedValue, addFocusedValueToBulk,
    renamePlaybook: (oldName, newName) => { renamePlaybook(oldName, newName); refreshPlaybooks(); },
    deletePlaybook: (name) => { deletePlaybook(name); refreshPlaybooks(); },
    runPlaybookNow: (name, value) => runPlaybook(name, value),
  };
}
