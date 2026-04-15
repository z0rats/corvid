import React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useTheme, alpha } from '@mui/material/styles';
import { getTierColor, getTierLabel, generateKeyDisplayName } from '../../../utils/settingsUtils';
import ApiKeyInput from '../../../components/forms/ApiKeyInput';

export default function ServiceCard({ serviceKey, service }) {
  const theme = useTheme();
  const isFullyConfigured = service.available;

  return (
    <Card elevation={0} sx={{ height: '100%', border: 'none' }}>
      <CardContent sx={{ p: 3 }}>
        <Stack spacing={2}>
          {/* Provider Header */}
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {service.name}
                </Typography>
                <Chip
                  label={getTierLabel(service.tier)}
                  size="small"
                  sx={{
                    backgroundColor: alpha(getTierColor(service.tier, theme), 0.08),
                    color: getTierColor(service.tier, theme),
                    fontWeight: 500,
                  }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5, mb: 2 }}>
                {service.description}
              </Typography>
            </Box>
            {isFullyConfigured && (
              <CheckCircleIcon sx={{ color: theme.palette.success.main }} />
            )}
          </Box>

          {/* Capabilities */}
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              Supported IoC Types
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {service.supported_ioc_types.map((capability) => (
                <Chip
                  key={capability}
                  label={capability}
                  size="small"
                  sx={{
                    fontWeight: 500,
                    fontSize: '0.75rem',
                    color: theme.palette.text.secondary,
                    backgroundColor: theme.palette.action.hover,
                  }}
                />
              ))}
            </Box>
          </Box>

          {/* API Key Inputs */}
          {service.required_keys.length === 0 ? (
            <Box sx={{ p: 2, backgroundColor: alpha(theme.palette.success.main, 0.03), borderRadius: 1 }}>
              <Typography variant="body2" color="success.main" sx={{ fontWeight: 500 }}>
                No API key required - Ready to use
              </Typography>
            </Box>
          ) : (
            service.required_keys.map((keyName) => {
              const keyDisplayName = generateKeyDisplayName(keyName, service.name);
              const relatedKeys = service.required_keys.filter(k => k !== keyName);

              return (
                <ApiKeyInput
                  key={keyName}
                  name={keyName}
                  description={keyDisplayName}
                  link={service.documentation_url}
                  relatedKeys={relatedKeys}
                />
              );
            })
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
