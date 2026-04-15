import React from 'react';
import { useAtomValue } from 'jotai';
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
  const theme = useTheme();
  const appVersion = useAtomValue(appVersionAtom);

  return (
    <Box>
      {/* Main About Card */}
      <Card elevation={0} sx={{ p: 2, mb: 1, borderRadius: 1, border: 'none', backgroundColor: theme.palette.background.paper }}>
        <Typography variant="h4" component="h2" gutterBottom>
          About - OSINT Toolkit {appVersion && `v${appVersion}`}
        </Typography>
        <Typography variant="body1" paragraph>
          OSINT Toolkit is a self-hostable, on-demand analysis platform designed
          for security specialists. It consolidates various security tools into
          a single, easy-to-use environment, streamlining everyday investigative
          tasks. Optimized for single-user operation, OSINT Toolkit runs locally
          in a Docker container and is not intended for long-term data storage
          or management. Instead, it focuses on accelerating daily workflows,
          such as news aggregation and analysis, IOC and email investigations,
          and the creation of threat detection rules. To further enhance
          efficiency, OSINT Toolkit integrates generative AI capabilities,
          providing additional support for analysis and decision-making. Beyond
          its practical applications, the project also serves as a personal
          playground for experimenting with new technologies and automation
          possibilities, potentially laying the foundation for a future
          commercial cloud platform.
        </Typography>
        <Typography variant="body1">
          The name OSINT Toolkit is a temporary name. The name may be changed in
          the future.
        </Typography>
      </Card>

      {/* Made by Card */}
      <Card elevation={0} sx={{ p: 2, mb: 1, borderRadius: 1, border: 'none', backgroundColor: theme.palette.background.paper }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Made by Lars Ursprung
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
          Donate to support the development
        </Typography>
        <Typography variant="body1" paragraph>
          If you want to support the development of OSINT Toolkit, you can
          donate using a service of your choice.
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
