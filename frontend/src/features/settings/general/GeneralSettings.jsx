import { useId, useMemo } from 'react';
import { useAtom, useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
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
import { generalSettingsState, themeModeAtom } from '../../../core/state/atoms';
import { useGeneralSettings } from '../hooks/api/useGeneralSettings';
import { useCommandPaletteSettings } from '../hooks/api/useCommandPaletteSettings';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import NotificationSnackbar from '../components/ui/NotificationSnackbar';

const LANGUAGES = ['en', 'ru'];
const THEMES = ['light', 'dark'];
const START_SCREENS = ['search', 'newsfeed'];

/** A labelled select whose visible label is also the combobox's accessible name (via labelId). */
function SettingSelect({ label, helper, value, options, optionLabel, onChange, disabled }) {
  const labelId = useId();
  return (
    <Box>
      <Typography id={labelId} variant="body1" gutterBottom>{label}</Typography>
      {/* Fixed width, helper outside the control: inside it, a long helper widened that one
          select past the others. */}
      <FormControl sx={{ width: 240 }}>
        <Select labelId={labelId} value={value} onChange={onChange} disabled={disabled} size="small">
          {options.map((option) => (
            <MenuItem key={option} value={option}>{optionLabel(option)}</MenuItem>
          ))}
        </Select>
      </FormControl>
      {helper && <FormHelperText sx={{ ml: 0 }}>{helper}</FormHelperText>}
    </Box>
  );
}

/**
 * Settings → General: app-wide preferences that don't belong to any one feature - language,
 * theme, and what `/` opens to. Start screen/tiles share the command-palette settings endpoint
 * (same GeneralSettings row), they're just grouped here since they're what a user looks for.
 */
export default function GeneralSettings() {
  const { t } = useTranslation();
  const theme = useTheme();
  const generalSettings = useAtomValue(generalSettingsState);
  const [themeMode, setThemeMode] = useAtom(themeModeAtom);
  const { loading: languageLoading, updateLanguage } = useGeneralSettings();
  const { loading: paletteLoading, updateCommandPaletteSettings } = useCommandPaletteSettings();
  const { notification, showNotification, hideNotification } = useNotification();

  const cardStyle = useMemo(() => ({
    p: 1,
    pl: 2,
    m: 1,
    boxShadow: '0',
    backgroundColor: theme.palette.background.card,
    borderRadius: 1,
  }), [theme.palette.background.card]);

  const notify = (result) => showNotification(result.message, result.success ? 'success' : 'error');

  const handleLanguageChange = async (event) => notify(await updateLanguage(event.target.value));
  const handleStartScreenChange = async (event) => notify(
    await updateCommandPaletteSettings({ startScreen: event.target.value }),
  );
  const handleAlwaysTilesChange = async () => notify(await updateCommandPaletteSettings({
    // Negate the *defaulted* value shown in the switch, not the possibly-undefined raw value.
    alwaysTiles: !(generalSettings?.always_tiles ?? false),
  }));

  return (
    <Box>
      <Card sx={cardStyle}>
        <Typography variant="h4" component="h2" gutterBottom>
          {t('settings.general.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('settings.general.description')}
        </Typography>
      </Card>

      <Card sx={cardStyle}>
        <Stack spacing={3}>
          <SettingSelect
            label={t('settings.general.language')}
            helper={t('settings.general.languageHelper')}
            value={generalSettings?.language ?? 'en'}
            options={LANGUAGES}
            optionLabel={(lang) => t(`settings.general.languageOptions.${lang}`)}
            onChange={handleLanguageChange}
            disabled={languageLoading}
          />

          <SettingSelect
            label={t('settings.general.theme')}
            value={themeMode}
            options={THEMES}
            optionLabel={(mode) => t(`settings.general.themeOptions.${mode}`)}
            onChange={(event) => setThemeMode(event.target.value)}
          />

          <SettingSelect
            label={t('settings.general.startScreen')}
            helper={t('settings.general.startScreenHelper')}
            value={generalSettings?.start_screen ?? 'search'}
            options={START_SCREENS}
            optionLabel={(screen) => t(`settings.general.startScreenOptions.${screen}`)}
            onChange={handleStartScreenChange}
            disabled={paletteLoading}
          />

          <Box>
            <FormControlLabel
              control={(
                <Switch
                  checked={generalSettings?.always_tiles ?? false}
                  onChange={handleAlwaysTilesChange}
                  disabled={paletteLoading}
                />
              )}
              label={t('settings.general.alwaysTiles')}
            />
            <FormHelperText sx={{ ml: 0 }}>{t('settings.general.alwaysTilesHelper')}</FormHelperText>
          </Box>
        </Stack>
      </Card>

      <NotificationSnackbar notification={notification} onClose={hideNotification} />
    </Box>
  );
}
