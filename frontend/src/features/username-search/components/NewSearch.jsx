import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import SearchForm from './SearchForm';
import LiveScanView from './LiveScanView';
import ToolInfoBanner from './ToolInfoBanner';
import { useUsernameSearchScan } from '../hooks/useUsernameSearchScan';

export default function NewSearch() {
  const { t } = useTranslation('usernameSearch');
  const scan = useUsernameSearchScan();

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{t('page.title')}</Typography>
      <ToolInfoBanner />
      <SearchForm onSearch={scan.startScan} disabled={scan.phase === 'running'} />
      {scan.phase !== 'idle' && <LiveScanView scan={scan} />}
    </Box>
  );
}
