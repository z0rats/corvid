import { useId, useMemo, useState } from 'react';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { generalSettingsState } from '../../../core/state/atoms';
import { useCommandPaletteSettings } from '../hooks/api/useCommandPaletteSettings';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import NotificationSnackbar from '../components/ui/NotificationSnackbar';
import { buildCommandRegistry, resolveEntryPath } from '../../../core/config/commandRegistry';
import { detectIocType } from '../../../core/utils/iocTypeDetection';
import { buildPrefillUrl } from '../../../core/utils/crossFeatureNav';
import {
  getPlaybooks, renamePlaybook, deletePlaybook, addRecent,
} from '../../../core/utils/commandPaletteStorage';
import PlaybookManage from '../../../core/components/ui/CommandPalette/PlaybookManage';

/**
 * Settings → Command Palette tab (i18nKey nav.settingsTabs.commandPalette; "Управление" in the
 * Russian locale). Backed by the 3 new GeneralSettings columns
 * (auto_open_on_single_match/start_screen/always_tiles) plus playbook management, which is
 * otherwise only reachable via >playbook:manage in the palette itself.
 */
export default function CommandPaletteSettings() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const generalSettings = useAtomValue(generalSettingsState);
  const theme = useTheme();
  const startScreenSelectId = useId();

  const { loading, updateCommandPaletteSettings } = useCommandPaletteSettings();
  const { notification, showNotification, hideNotification } = useNotification();

  const registry = useMemo(() => buildCommandRegistry(t), [t]);
  const [playbooks, setPlaybooks] = useState(getPlaybooks);
  const refreshPlaybooks = () => setPlaybooks(getPlaybooks());

  const cardStyle = useMemo(() => ({
    p: 1,
    pl: 2,
    m: 1,
    boxShadow: '0',
    backgroundColor: theme.palette.background.card,
    borderRadius: 1,
  }), [theme.palette.background.card]);

  const applyUpdate = async (updates) => {
    const result = await updateCommandPaletteSettings(updates);
    showNotification(result.message, result.success ? 'success' : 'error');
  };

  const handleAutoOpenChange = () => applyUpdate({
    // Negate the *defaulted* value shown in the switch, not the possibly-undefined raw value —
    // otherwise the first toggle from an unset default silently sends the same value back.
    autoOpenOnSingleMatch: !(generalSettings?.auto_open_on_single_match ?? true),
  });

  const handleStartScreenChange = (event) => applyUpdate({ startScreen: event.target.value });

  const handleAlwaysTilesChange = () => applyUpdate({
    alwaysTiles: !(generalSettings?.always_tiles ?? false),
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
      <Card sx={cardStyle}>
        <Typography variant="h4" component="h2" gutterBottom>
          {t('settings.commandPalette.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('settings.commandPalette.description')}
        </Typography>
      </Card>

      <Card sx={cardStyle}>
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
            <Typography variant="body1" gutterBottom>
              {t('settings.commandPalette.startScreen')}
            </Typography>
            <FormControl sx={{ minWidth: 200 }}>
              <Select
                id={startScreenSelectId}
                value={generalSettings?.start_screen ?? 'search'}
                onChange={handleStartScreenChange}
                disabled={loading}
                size="small"
                slotProps={{ htmlInput: { 'aria-label': t('settings.commandPalette.startScreen') } }}
              >
                <MenuItem value="search">{t('settings.commandPalette.startScreenOptions.search')}</MenuItem>
                <MenuItem value="newsfeed">{t('settings.commandPalette.startScreenOptions.newsfeed')}</MenuItem>
              </Select>
              <FormHelperText>{t('settings.commandPalette.startScreenHelper')}</FormHelperText>
            </FormControl>
          </Box>

          <Box>
            <FormControlLabel
              control={(
                <Switch
                  checked={generalSettings?.always_tiles ?? false}
                  onChange={handleAlwaysTilesChange}
                  disabled={loading}
                />
              )}
              label={t('settings.commandPalette.alwaysTiles')}
            />
            <FormHelperText sx={{ ml: 0 }}>
              {t('settings.commandPalette.alwaysTilesHelper')}
            </FormHelperText>
          </Box>

          <Box>
            <Typography variant="body1">{t('settings.commandPalette.recents')}</Typography>
            <FormHelperText sx={{ ml: 0 }}>{t('settings.commandPalette.recentsHelper')}</FormHelperText>
          </Box>
        </Stack>
      </Card>

      <Card sx={cardStyle}>
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
