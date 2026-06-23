import React, { useState } from 'react';
import Box from '@mui/material/Box';
import { useImageAnalysis } from './hooks/api/useImageAnalysis';
import ImageUploadForm from './components/forms/ImageUploadForm';
import WelcomeScreen from './components/ui/WelcomeScreen';
import ImageAnalysisResult from './components/ui/ImageAnalysisResult';

export default function ImageTools() {
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
          imageUrl={imageUrl}
          onImageUrlChange={setImageUrl}
          isLoading={isLoading}
          uploadProgress={uploadProgress}
          error={error}
        />
      </Box>

      {result ? (
        <ImageAnalysisResult result={result} previewUrl={previewUrl} imageUrl={imageUrl} />
      ) : (
        <WelcomeScreen />
      )}
    </Box>
  );
}
