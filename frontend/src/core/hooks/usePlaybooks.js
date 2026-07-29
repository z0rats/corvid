import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  getPlaybooks, savePlaybook,
  renamePlaybook as renamePlaybookStorage,
  deletePlaybook as deletePlaybookStorage,
} from '../utils/commandPaletteStorage';

/**
 * Recording lifecycle + saved-playbook CRUD + replay. `onOpenEntry` is the composing core hook's
 * "actually open this tool" step (navigate/recents/breadcrumb-for-this-entry/close) — runPlaybook
 * delegates to it rather than duplicating that logic, and deliberately uses the *non*-recording-
 * aware variant, matching the original behavior where replaying a playbook never feeds itself
 * back into an active recording session.
 */
export function usePlaybooks(registry, { onOpenEntry, setBreadcrumbs, showNotice }) {
  const { t } = useTranslation('commandPalette');

  const [isRecording, setIsRecording] = useState(false);
  const [recordingSteps, setRecordingSteps] = useState([]);
  const [pendingRecordStopName, setPendingRecordStopName] = useState(false);
  const [playbooks, setPlaybooks] = useState(getPlaybooks);

  const refreshPlaybooks = useCallback(() => setPlaybooks(getPlaybooks()), []);

  const startRecording = useCallback(() => {
    setIsRecording(true);
    setRecordingSteps([]);
  }, []);

  const recordStep = useCallback((toolId) => {
    setRecordingSteps((prev) => (prev.includes(toolId) ? prev : [...prev, toolId]));
  }, []);

  const requestRecordStopName = useCallback(() => setPendingRecordStopName(true), []);
  const cancelRecordStopPrompt = useCallback(() => setPendingRecordStopName(false), []);

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
    onOpenEntry(firstEntry, value); // pushes firstEntry's own breadcrumb via the shared open path
    if (restIds.length > 0) {
      setBreadcrumbs((prev) => [
        ...prev,
        ...restIds.map((id) => {
          const entry = registry.find((e) => e.id === id);
          return { label: entry?.label ?? id, toolId: id, pending: true };
        }),
      ]);
    }
  }, [playbooks, registry, onOpenEntry, setBreadcrumbs, showNotice, t]);

  const renamePlaybook = useCallback((oldName, newName) => {
    renamePlaybookStorage(oldName, newName);
    refreshPlaybooks();
  }, [refreshPlaybooks]);

  const deletePlaybook = useCallback((name) => {
    deletePlaybookStorage(name);
    refreshPlaybooks();
  }, [refreshPlaybooks]);

  return {
    isRecording, recordingSteps, pendingRecordStopName,
    startRecording, recordStep, finishRecording, requestRecordStopName, cancelRecordStopPrompt,
    playbooks, refreshPlaybooks, renamePlaybook, deletePlaybook, runPlaybook,
  };
}
