import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import DownloadIcon from '@mui/icons-material/Download';

import { downloadFromApi } from '../../services/apiDownload';
import { createLogger } from '../../utils/logger';

const logger = createLogger('ApiDownloadButtons');

/**
 * One outlined button per format, each downloading `request(format)` = `{ path, params,
 * fallbackName }` via `downloadFromApi`, with an inline error if a download fails.
 */
export default function ApiDownloadButtons({ formats, request, sx }) {
  const { t } = useTranslation();
  const [failed, setFailed] = useState(false);

  const download = async (format) => {
    setFailed(false);
    const { path, ...options } = request(format);
    try {
      await downloadFromApi(path, options);
    } catch (err) {
      logger.error(`Failed to download ${path}:`, err);
      setFailed(true);
    }
  };

  return (
    <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', alignItems: 'center', rowGap: 1, ...sx }}>
      {formats.map((format) => (
        <Button
          key={format}
          size="small"
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={() => download(format)}
        >
          {format.toUpperCase()}
        </Button>
      ))}
      {failed && (
        <Typography variant="body2" color="error">{t('download.failed')}</Typography>
      )}
    </Stack>
  );
}
