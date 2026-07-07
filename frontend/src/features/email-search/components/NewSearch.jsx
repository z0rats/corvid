import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import SearchForm from './SearchForm';
import LiveScanView from './LiveScanView';
import ToolInfoBanner from './ToolInfoBanner';
import { useEmailSearchScan } from '../hooks/useEmailSearchScan';

export default function NewSearch() {
  const { t } = useTranslation('emailSearch');
  const scan = useEmailSearchScan();

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{t('page.title')}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('page.description')}
      </Typography>
      <ToolInfoBanner />
      <SearchForm onSearch={scan.startScan} disabled={scan.phase === 'running'} />
      {scan.phase !== 'idle' && <LiveScanView scan={scan} />}
    </Box>
  );
}
