import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';

import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('UsernameSearchToolInfo');

export default function ToolInfoBanner() {
  const { t } = useTranslation('usernameSearch');
  const [infoList, setInfoList] = useState(null);

  useEffect(() => {
    let ignore = false;
    usernameSearchApi.getInfo()
      .then((data) => { if (!ignore) setInfoList(data); })
      .catch((err) => logger.error('Failed to load tool info:', err));
    return () => { ignore = true; };
  }, []);

  if (!infoList) return null;

  return (
    <Box sx={{ mb: 2 }}>
      {infoList.map((info) => (
        <Typography key={info.tool} variant="caption" color="text.secondary" sx={{ display: 'block' }}>
          {t('toolInfo.poweredBy', { tool: info.tool, version: info.version })}
          {' — '}
          {info.db_last_updated_at
            ? t('toolInfo.sitesUpdated', { count: info.site_count, date: new Date(info.db_last_updated_at).toLocaleString() })
            : t('toolInfo.sitesBundled', { count: info.site_count })}
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
      ))}
    </Box>
  );
}
