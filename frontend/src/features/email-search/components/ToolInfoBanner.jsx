import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';

import { emailSearchApi } from '../services/api/emailSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('EmailSearchToolInfo');

export default function ToolInfoBanner({ source = 'mailcat' }) {
  const { t } = useTranslation('emailSearch');
  const [info, setInfo] = useState(null);

  useEffect(() => {
    let ignore = false;
    setInfo(null);
    emailSearchApi.getInfo(source)
      .then((data) => { if (!ignore) setInfo(data); })
      .catch((err) => logger.error('Failed to load tool info:', err));
    return () => { ignore = true; };
  }, [source]);

  if (!info) return null;

  if (info.available === false) {
    return <Alert severity="error" sx={{ mb: 2 }}>{t('toolInfo.notInstalled', { tool: info.tool })}</Alert>;
  }

  return (
    <Box sx={{ mb: 2 }}>
      {info.blocked_reason && (
        <Alert severity="warning" sx={{ mb: 1 }}>{info.blocked_reason}</Alert>
      )}
      <Typography variant="caption" color="text.secondary" display="block">
        {t('toolInfo.poweredBy', { tool: info.tool, version: info.version })}
        {' — '}
        {t('toolInfo.providerCount', { count: info.provider_count })}
        {info.update_available && (
          <Chip
            size="small"
            color="info"
            variant="outlined"
            label={t('toolInfo.updateAvailable', { version: info.latest_version })}
            sx={{ ml: 1, height: 18 }}
          />
        )}
      </Typography>
    </Box>
  );
}
