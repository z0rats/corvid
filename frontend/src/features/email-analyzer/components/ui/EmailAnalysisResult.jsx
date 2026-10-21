import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import DownloadIcon from '@mui/icons-material/Download';
import GeneralInfo from './GeneralInfo';
import SecurityCheck from './SecurityCheck';
import Attachments from './Attachments';
import Urls from './Urls';
import Hops from './Hops';
import Header from './Header';
import MessageBody from './MessageBody';
import { emailAnalyzerApi } from '../../services/api/emailAnalyzerApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('EmailAnalysisResult');
const EXPORT_FORMATS = ['html', 'pdf'];

export default function EmailAnalysisResult({ result }) {
  const { t, i18n } = useTranslation('emailAnalyzer');
  const [exportFailed, setExportFailed] = useState(false);
  const [exporting, setExporting] = useState(false);
  const locale = i18n.language?.startsWith('ru') ? 'ru' : 'en';

  if (!result) {
    return null;
  }

  // One export at a time: a slow failure landing after a later success would otherwise flag
  // the wrong request.
  const handleExport = async (format) => {
    setExportFailed(false);
    setExporting(true);
    try {
      const blob = await emailAnalyzerApi.exportReport(result, format, locale);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `email-analysis.${format}`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      logger.error('Failed to export email analysis report:', err);
      setExportFailed(true);
    } finally {
      setExporting(false);
    }
  };

  return (
    <>
      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap' }}>
        {EXPORT_FORMATS.map((fmt) => (
          <Button
            key={fmt}
            size="small"
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => handleExport(fmt)}
            disabled={exporting}
          >
            {fmt.toUpperCase()}
          </Button>
        ))}
      </Stack>

      {exportFailed && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setExportFailed(false)}>
          {t('exportFailed')}
        </Alert>
      )}

      <GeneralInfo
        result={result["basic_info"]}
        hashes={result["eml_hashes"]}
      />

      <SecurityCheck result={result["warnings"]} />

      <Attachments result={result["attachments"]} />

      <Urls result={result["urls"]} />

      <Hops result={result["hops"]} />

      <Header result={result["headers"]} />

      <MessageBody result={result["message_text"]} />
    </>
  );
}
