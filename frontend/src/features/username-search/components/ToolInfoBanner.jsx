import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Typography from '@mui/material/Typography';

import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('UsernameSearchToolInfo');

export default function ToolInfoBanner() {
  const { t } = useTranslation('usernameSearch');
  const [info, setInfo] = useState(null);

  useEffect(() => {
    let ignore = false;
    usernameSearchApi.getInfo()
      .then((data) => { if (!ignore) setInfo(data); })
      .catch((err) => logger.error('Failed to load tool info:', err));
    return () => { ignore = true; };
  }, []);

  if (!info) return null;

  return (
    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
      {t('toolInfo.poweredBy', { tool: info.tool, version: info.version })}
      {' — '}
      {info.db_last_updated_at
        ? t('toolInfo.sitesUpdated', { count: info.site_count, date: new Date(info.db_last_updated_at).toLocaleString() })
        : t('toolInfo.sitesBundled', { count: info.site_count })}
    </Typography>
  );
}
