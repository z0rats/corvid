import { useState, useMemo } from 'react';
import Box from '@mui/material/Box';
import AppSnackbar from '../../../core/components/ui/AppSnackbar';
import FileUploadZone from './components/ui/FileUploadZone';
import StatisticsOverview from './components/ui/StatisticsOverview';
import WelcomeScreen from './components/ui/WelcomeScreen';
import ResultRows from './components/ui/ResultRows';
import { useExtractor } from './hooks/useExtractor';
import { IOC_CATEGORIES } from './constants/iocCategories';
import { logger } from '../shared/utils/logger';

export default function IocExtractor() {
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  const {
    extractedData,
    uploadProgress,
    isLoading,
    hasResults,
    extractFromFile,
    copyAllIOCs,
    exportAllIOCs,
    statistics
  } = useExtractor();

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleFileUpload = async (file) => {
    try {
      await extractFromFile(file);
      showSnackbar('IOC extraction completed successfully');
    } catch (err) {
      logger.error('File upload failed', { error: err.message });
      showSnackbar(err.message || 'Failed to extract IOCs from file', 'error');
    }
  };

  const handleCopyAll = async () => {
    try {
      const result = await copyAllIOCs();
      showSnackbar(result.message);
    } catch (err) {
      showSnackbar(err.message || 'Failed to copy IOCs', 'error');
    }
  };

  const handleExportAll = () => {
    try {
      const result = exportAllIOCs();
      showSnackbar(result.message);
    } catch (err) {
      showSnackbar(err.message || 'Failed to export IOCs', 'error');
    }
  };

  const categories = useMemo(() => IOC_CATEGORIES.map((category) => ({
    ...category,
    list: extractedData?.[category.dataKey] || [],
    count: extractedData?.statistics?.[category.dataKey] || 0,
    icon: <category.icon />
  })), [extractedData]);

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <FileUploadZone
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
          uploadProgress={uploadProgress}
        />
      </Box>

      {hasResults ? (
        <Box sx={{ mt: 2 }}>
          <StatisticsOverview
            statistics={statistics}
            onCopyAll={handleCopyAll}
            onExportAll={handleExportAll}
          />

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {categories.map((category) => (
              <ResultRows
                key={category.type}
                title={category.title}
                type={category.type}
                list={category.list}
                count={category.count}
                icon={category.icon}
              />
            ))}
          </Box>
        </Box>
      ) : (
        <WelcomeScreen />
      )}

      <AppSnackbar
        open={snackbar.open}
        message={snackbar.message}
        severity={snackbar.severity}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      />
    </Box>
  );
}
