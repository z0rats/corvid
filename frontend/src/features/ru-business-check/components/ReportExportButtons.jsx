import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import DownloadIcon from '@mui/icons-material/Download';

import { ruBusinessCheckApi } from '../services/api/ruBusinessCheckApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('RuBusinessCheckReportExport');
const EXPORT_FORMATS = ['html', 'pdf'];

export default function ReportExportButtons({ searchId }) {
  const handleExport = async (format) => {
    try {
      const blob = await ruBusinessCheckApi.exportReport(searchId, format);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ru-business-check-${searchId}.${format}`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      logger.error('Failed to export report:', err);
    }
  };

  return (
    <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap' }}>
      {EXPORT_FORMATS.map((fmt) => (
        <Button
          key={fmt}
          size="small"
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => handleExport(fmt)}
        >
          {fmt.toUpperCase()}
        </Button>
      ))}
    </Stack>
  );
}
