import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import ImageSearchIcon from '@mui/icons-material/ImageSearch';
import { useImageAnalysis } from './hooks/api/useImageAnalysis';
import ImageUploadForm from './components/forms/ImageUploadForm';
import WelcomeScreen from './components/ui/WelcomeScreen';
import ImageAnalysisResult from './components/ui/ImageAnalysisResult';
import ReverseSearchLinks from './components/ui/ReverseSearchLinks';

export default function ImageTools() {
  const { t } = useTranslation('imageTools');
  const [imageUrl, setImageUrl] = useState('');
  const {
    result,
    previewUrl,
    isLoading,
    error,
    uploadProgress,
    analyzeImage,
  } = useImageAnalysis();

  const handleFileUpload = (file) => {
    analyzeImage(file);
  };

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <ImageUploadForm
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
          uploadProgress={uploadProgress}
          error={error}
        />
      </Box>

      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Box display="flex" alignItems="center" sx={{ mb: 1 }}>
          <ImageSearchIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="subtitle1" fontWeight="medium">{t('reverseSearch.title')}</Typography>
        </Box>
        <TextField
          label={t('reverseSearch.urlLabel')}
          placeholder={t('reverseSearch.urlPlaceholder')}
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
          size="small"
          fullWidth
          sx={{ mb: 2 }}
        />
        <ReverseSearchLinks imageUrl={imageUrl} />
      </Paper>

      {result ? (
        <ImageAnalysisResult result={result} previewUrl={previewUrl} />
      ) : (
        <WelcomeScreen />
      )}
    </Box>
  );
}
