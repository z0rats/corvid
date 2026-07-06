import React from 'react';
import { useTranslation } from 'react-i18next';
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
  const { i18n } = useTranslation('emailAnalyzer');
  const locale = i18n.language?.startsWith('ru') ? 'ru' : 'en';

  if (!result) {
    return null;
  }

  const handleExport = async (format) => {
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
          >
            {fmt.toUpperCase()}
          </Button>
        ))}
      </Stack>

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
