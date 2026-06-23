import React from 'react';
import { useDropzone } from 'react-dropzone';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import { IMAGE_CONSTANTS } from '../../constants/imageConstants';
import { imageUtils } from '../../utils/imageUtils';

export default function ImageUploadForm({
  onFileUpload,
  imageUrl,
  onImageUrlChange,
  isLoading,
  uploadProgress,
  error
}) {
  const {
    getRootProps,
    getInputProps,
    acceptedFiles,
    isFocused,
    isDragAccept,
  } = useDropzone({
    accept: IMAGE_CONSTANTS.ACCEPTED_FILE_TYPES,
    maxSize: IMAGE_CONSTANTS.FILE_UPLOAD.MAX_SIZE,
    multiple: false
  });

  const acceptedFileItems = acceptedFiles.map((file) => (
    <Typography key={file.path} variant="body2" component="span" fontWeight="bold">
      {file.path} - {imageUtils.formatFileSize(file.size)}
    </Typography>
  ));

  const handleAnalyze = () => {
    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0]);
    }
  };

  return (
    <Paper
      elevation={1}
      sx={{
        p: 2,
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
        <UploadFileIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 500 }}>
          Image Upload
        </Typography>
      </Box>

      <Box
        {...getRootProps()}
        sx={{
          border: '2px dashed',
          borderColor: isFocused || isDragAccept ? 'primary.main' : 'grey.300',
          borderRadius: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 140,
          cursor: isLoading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          backgroundColor: isFocused || isDragAccept ? 'primary.50' : 'transparent',
          '&:hover': {
            borderColor: isLoading ? 'grey.300' : 'primary.main',
            backgroundColor: isLoading ? 'grey.50' : 'primary.50'
          }
        }}
      >
        <input {...getInputProps()} disabled={isLoading} />
        <UploadFileIcon
          sx={{
            fontSize: 40,
            color: isLoading ? 'grey.400' : 'grey.500',
            mb: 1
          }}
        />
        <Typography
          variant="body2"
          textAlign="center"
          sx={{
            color: isLoading ? 'grey.400' : 'text.secondary',
            px: 1,
            lineHeight: 1.3
          }}
        >
          Drag 'n' drop an image here, or click to select a file
        </Typography>
        <Typography
          variant="caption"
          textAlign="center"
          sx={{
            color: isLoading ? 'grey.400' : 'text.secondary',
            mt: 0.5
          }}
        >
          (JPEG, PNG, TIFF, WEBP, HEIC, BMP, GIF)
        </Typography>
      </Box>

      {uploadProgress > 0 && (
        <LinearProgress
          sx={{ mt: 2 }}
          variant="determinate"
          value={uploadProgress}
        />
      )}

      {acceptedFileItems.length > 0 && (
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {acceptedFileItems}
          </Typography>
        </Box>
      )}

      {error && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="error">
            {error}
          </Typography>
        </Box>
      )}

      <TextField
        label="Image URL (optional, enables reverse-search links)"
        placeholder="https://example.com/photo.jpg"
        value={imageUrl}
        onChange={(e) => onImageUrlChange(e.target.value)}
        size="small"
        fullWidth
        sx={{ mt: 2 }}
        disabled={isLoading}
      />

      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleAnalyze}
          disabled={isLoading || acceptedFiles.length === 0}
          size="medium"
          sx={{ minWidth: 140 }}
        >
          {isLoading ? <CircularProgress size={24} /> : "Analyze"}
        </Button>
      </Box>
    </Paper>
  );
}
