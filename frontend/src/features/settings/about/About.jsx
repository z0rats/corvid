import React from 'react';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import GitHubIcon from '@mui/icons-material/GitHub';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import { useTheme } from '@mui/material/styles';
import { appVersionAtom } from '../../../core/state/atoms';

import liberapay from './images/donate_liberapay.png';
import kofi from './images/donate_kofi.png';
import patreon from './images/donate_patreon.png';

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

      {/* Made by Card */}
      <Card elevation={0} sx={{ p: 2, mb: 1, borderRadius: 1, border: 'none', backgroundColor: theme.palette.background.paper }}>
        <Typography variant="h5" component="h2" gutterBottom>
          {t('about.madeBy')}
        </Typography>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} alignItems="center">
            <GitHubIcon />
            <Typography variant="body1">
              https://github.com/dev-lu
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <LinkedInIcon />
            <Typography variant="body1">
              https://linkedin.com/in/lars-ursprung
            </Typography>
          </Stack>
        </Stack>
      </Card>

      {/* Donate Card */}
      <Card elevation={0} sx={{ p: 2, mb: 1, borderRadius: 1, border: 'none', backgroundColor: theme.palette.background.paper }}>
        <Typography variant="h5" component="h2" gutterBottom>
          {t('about.donateTitle')}
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          {t('about.donateBody')}
        </Typography>
        
        <Stack direction="row" spacing={4} sx={{ mt: 2 }}>
          <Box
            component="a"
            href="https://liberapay.com/Dev-LU/donate"
            target="_blank"
            rel="noopener noreferrer"
            sx={{ display: 'block' }}
          >
            <Box
              component="img"
              src={liberapay}
              alt="Donate using Liberapay"
              sx={{ height: 60 }}
            />
          </Box>
          <Box
            component="a"
            href="https://ko-fi.com/devlu"
            target="_blank"
            rel="noopener noreferrer"
            sx={{ display: 'block' }}
          >
            <Box
              component="img"
              src={kofi}
              alt="Donate using Ko-fi"
              sx={{ height: 60 }}
            />
          </Box>
          <Box
            component="a"
            href="https://patreon.com/devlu"
            target="_blank"
            rel="noopener noreferrer"
            sx={{ display: 'block' }}
          >
            <Box
              component="img"
              src={patreon}
              alt="Donate using Patreon"
              sx={{ height: 60 }}
            />
          </Box>
        </Stack>
      </Card>
    </Box>
  );
}
