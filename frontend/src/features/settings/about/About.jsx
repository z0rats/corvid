import React from 'react';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { appVersionAtom } from '../../../core/state/atoms';

export default function About() {
  const { t } = useTranslation('settings');
  const theme = useTheme();
  const appVersion = useAtomValue(appVersionAtom);

  return (
    <Box>
      {/* Main About Card */}
      <Card elevation={0} sx={{ p: 2, mb: 1, borderRadius: 1, border: 'none', backgroundColor: theme.palette.background.paper }}>
        <Typography variant="h4" component="h2" gutterBottom>
          {t('about.title')} {appVersion && `v${appVersion}`}
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          {t('about.body')}
        </Typography>
        <Typography variant="body1">
          {t('about.nameNote')}
        </Typography>
      </Card>
    </Box>
  );
}
