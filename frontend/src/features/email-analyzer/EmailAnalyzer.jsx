import React from 'react';
import Box from '@mui/material/Box';
import { useEmailAnalysis } from './hooks/api/useEmailAnalysis';
import EmailUploadForm from './components/forms/EmailUploadForm';
import WelcomeScreen from './components/ui/WelcomeScreen';
import EmailAnalysisResult from './components/ui/EmailAnalysisResult';

export default function EmailAnalyzer() {
  const {
    result,
    isLoading,
    error,
    uploadProgress,
    analyzeEmail,
  } = useEmailAnalysis();

  const handleFileUpload = (file) => {
    analyzeEmail(file);
  };

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <EmailUploadForm
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
          uploadProgress={uploadProgress}
          error={error}
        />
      </Box>

      {result ? (
        <EmailAnalysisResult result={result} />
      ) : (
        <WelcomeScreen />
      )}
    </Box>
  );
}
