import { useMemo, useState } from 'react';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import { generalSettingsState } from '../../../core/state/atoms';
import { useCommandPaletteSettings } from '../hooks/api/useCommandPaletteSettings';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import NotificationSnackbar from '../components/ui/NotificationSnackbar';
import { SETTINGS_CARD_SX } from '../constants/settingsConstants';
import { buildCommandRegistry, resolveEntryPath } from '../../../core/config/commandRegistry';
import { detectIocType } from '../../../core/utils/iocTypeDetection';
import { buildPrefillUrl } from '../../../core/utils/crossFeatureNav';
import {
  getPlaybooks, renamePlaybook, deletePlaybook, addRecent,
} from '../../../core/utils/commandPaletteStorage';
import PlaybookManage from '../../../core/components/ui/CommandPalette/PlaybookManage';

/**
 * Settings → Command Palette tab (i18nKey nav.settingsTabs.commandPalette; "Управление" in the
 * Russian locale): auto_open_on_single_match plus playbook management, which is otherwise only
 * reachable via >playbook:manage in the palette itself. The same endpoint's start_screen and
 * always_tiles columns are edited from Settings → General instead.
 */
export default function CommandPaletteSettings() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const generalSettings = useAtomValue(generalSettingsState);

  const { loading, updateCommandPaletteSettings } = useCommandPaletteSettings();
  const { notification, showNotification, hideNotification } = useNotification();

  const registry = useMemo(() => buildCommandRegistry(t), [t]);
  const [playbooks, setPlaybooks] = useState(getPlaybooks);
  const refreshPlaybooks = () => setPlaybooks(getPlaybooks());

  const applyUpdate = async (updates) => {
    const result = await updateCommandPaletteSettings(updates);
    showNotification(result.message, result.success ? 'success' : 'error');
  };

  const handleAutoOpenChange = () => applyUpdate({
    // Negate the *defaulted* value shown in the switch, not the possibly-undefined raw value —
    // otherwise the first toggle from an unset default silently sends the same value back.
    autoOpenOnSingleMatch: !(generalSettings?.auto_open_on_single_match ?? true),
  });

  const handleRunPlaybookNow = (name, value) => {
    const playbook = playbooks.find((p) => p.name === name);
    if (!playbook || playbook.steps.length === 0) return;
    const entry = registry.find((e) => e.id === playbook.steps[0]);
    if (!entry) return;
    const iocType = value ? detectIocType(value) : undefined;
    const path = resolveEntryPath(entry, iocType);
    navigate(value ? buildPrefillUrl(path, value) : path);
    addRecent({ type: 'tool', toolId: entry.id, value: value || undefined });
  };

  return (
    <Box>
      <Card sx={SETTINGS_CARD_SX}>
        <Typography variant="h4" component="h2" gutterBottom>
          {t('settings.commandPalette.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('settings.commandPalette.description')}
        </Typography>
      </Card>

      <Card sx={SETTINGS_CARD_SX}>
        <Stack spacing={3}>
          <Box>
            <FormControlLabel
              control={(
                <Switch
                  checked={generalSettings?.auto_open_on_single_match ?? true}
                  onChange={handleAutoOpenChange}
                  disabled={loading}
                />
              )}
              label={t('settings.commandPalette.autoOpen')}
            />
            <FormHelperText sx={{ ml: 0 }}>
              {t('settings.commandPalette.autoOpenHelper')}
            </FormHelperText>
          </Box>

          <Box>
            <Typography variant="body1">{t('settings.commandPalette.recents')}</Typography>
            <FormHelperText sx={{ ml: 0 }}>{t('settings.commandPalette.recentsHelper')}</FormHelperText>
          </Box>
        </Stack>
      </Card>

      <Card sx={SETTINGS_CARD_SX}>
        <Typography variant="h5" component="h3" gutterBottom>
          {t('settings.commandPalette.playbooksTitle')}
        </Typography>
        <PlaybookManage
          playbooks={playbooks}
          registry={registry}
          onRename={(oldName, newName) => { renamePlaybook(oldName, newName); refreshPlaybooks(); }}
          onDelete={(name) => { deletePlaybook(name); refreshPlaybooks(); }}
          onRunNow={handleRunPlaybookNow}
        />
      </Card>

      <NotificationSnackbar
        notification={notification}
        onClose={hideNotification}
      />
    </Box>
  );
}
