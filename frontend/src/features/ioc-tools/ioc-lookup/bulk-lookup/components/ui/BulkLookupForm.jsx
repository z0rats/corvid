import React, { useCallback } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import TextFields from '@mui/icons-material/TextFields';
import UploadFileIcon from '@mui/icons-material/UploadFile';

const ALLOWED_MIME_TYPES = ['text/csv', 'text/markdown', 'text/plain'];
const ALLOWED_EXTENSIONS = ['.csv', '.md', '.txt'];

export default function BulkLookupForm({
  iocsInput,
  onInputChange,
  onSubmit,
  isSubmitDisabled,
  processing,
  hasEnabledServices,
  onFormError,
}) {
  const handleDragOver = useCallback((event) => {
    event.preventDefault();
  }, []);

  const handleDrop = useCallback((event) => {
    event.preventDefault();

    if (processing) return;

    const files = event.dataTransfer.files;
    if (files.length === 0) return;

    const file = files[0];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

    if (!ALLOWED_MIME_TYPES.includes(file.type) && !ALLOWED_EXTENSIONS.includes(fileExtension)) {
      onFormError('Invalid file type. Please drop a CSV, MD, or TXT file.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => onInputChange(e.target.result);
    reader.onerror = () => onFormError(`Error reading file: ${file.name}`);
    reader.readAsText(file);
  }, [processing, onInputChange, onFormError]);

  return (
    <Paper elevation={1} sx={{ p: 3, mb: 2 }}>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
              <TextFields sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 500 }}>
                IOC Input
              </Typography>
            </Box>
            <TextField
              label="Enter IOCs (one per line)"
              multiline
              fullWidth
              variant="outlined"
              value={iocsInput}
              onChange={(e) => onInputChange(e.target.value)}
              disabled={processing}
              size="small"
              sx={{
                flex: 1,
                '& .MuiOutlinedInput-root': {
                  fontSize: '0.875rem',
                  height: '168px',
                  alignItems: 'flex-start'
                },
                '& .MuiOutlinedInput-input': {
                  height: '100% !important',
                  overflow: 'auto !important'
                }
              }}
            />
          </Box>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
              <UploadFileIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 500 }}>
                File Upload
              </Typography>
            </Box>
            <Box
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              sx={{
                border: '2px dashed',
                borderColor: 'grey.300',
                borderRadius: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '168px',
                cursor: processing ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
                '&:hover': {
                  borderColor: processing ? 'grey.300' : 'primary.main',
                  backgroundColor: processing ? 'grey.50' : 'primary.50'
                }
              }}
            >
              <UploadFileIcon
                sx={{
                  fontSize: 40,
                  color: processing ? 'grey.400' : 'grey.500',
                  mb: 1
                }}
              />
              <Typography
                variant="body2"
                textAlign="center"
                sx={{
                  color: processing ? 'grey.400' : 'text.secondary',
                  px: 1,
                  lineHeight: 1.3
                }}
              >
                Drop files here
              </Typography>
              <Typography
                variant="caption"
                textAlign="center"
                sx={{
                  color: processing ? 'grey.400' : 'text.secondary',
                  mt: 0.5
                }}
              >
                (.txt, .csv, .md)
              </Typography>
            </Box>
          </Box>
        </Grid>

        <Grid size={12}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, mt: 1 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={onSubmit}
              disabled={isSubmitDisabled}
              size="medium"
              sx={{ minWidth: 140 }}
            >
              {processing ? 'Looking up...' : 'Analyze IOCs'}
            </Button>

            {!hasEnabledServices && (
              <Typography variant="body2" color="error" sx={{ textAlign: 'center' }}>
                Enable at least one service in settings above
              </Typography>
            )}
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
}
