import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { phoneSearchApi } from '../services/api/phoneSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('PhoneSearchToolInfo');

export default function ToolInfoBanner() {
  const { t } = useTranslation('phoneSearch');
  const [info, setInfo] = useState(null);

  useEffect(() => {
    let ignore = false;
    phoneSearchApi.getInfo()
      .then((data) => { if (!ignore) setInfo(data); })
      .catch((err) => logger.error('Failed to load tool info:', err));
    return () => { ignore = true; };
  }, []);

  if (!info) return null;

  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="caption" color="text.secondary" display="block">
        {t('toolInfo.providerCount', { count: info.provider_count })}
      </Typography>
    </Box>
  );
}
