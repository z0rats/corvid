import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import ClearIcon from '@mui/icons-material/Clear';
import CopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import ProcessIcon from '@mui/icons-material/PlayArrow';
import { useTranslation } from 'react-i18next';

const InputForm = ({
  inputText,
  onInputChange,
  operation,
  onProcess,
  onClear,
  onCopyAllResults,
  onDownloadCsv,
  hasResults
}) => {
  const { t } = useTranslation('iocTools');
  const lineCount = inputText.split('\n').filter(line => line.trim()).length;

  return (
    <>
      <TextField
        fullWidth
        multiline
        minRows={8}
        variant="outlined"
        sx={{ '& .MuiInputBase-inputMultiline': { resize: 'vertical' } }}
        label={operation === 'defang'
          ? t('iocDefanger.inputForm.labelDefang')
          : t('iocDefanger.inputForm.labelFang')
        }
        placeholder={operation === 'defang'
          ? "https://example.com\n192.168.1.1\nuser@domain.com\nmalware.exe"
          : "hxxps[://]example[.]com\n192[.]168[.]1[.]1\nuser[@]domain[.]com"
        }
        value={inputText}
        onChange={(e) => onInputChange(e.target.value)}
        helperText={t('iocDefanger.inputForm.helperText', { count: lineCount })}
      />

      <Stack direction="row" spacing={1} sx={{ mt: 1.5, justifyContent: 'flex-start' }}>
        {hasResults && (
          <Button
            size="small"
            variant="outlined"
            onClick={onCopyAllResults}
            startIcon={<CopyIcon />}
          >
            {t('iocDefanger.inputForm.copyAllResults')}
          </Button>
        )}
        {hasResults && (
          <Button
            size="small"
            variant="outlined"
            onClick={onDownloadCsv}
            startIcon={<DownloadIcon />}
          >
            {t('iocDefanger.inputForm.downloadCsv')}
          </Button>
        )}
        <Button
          size="small"
          variant="outlined"
          onClick={onClear}
          disabled={!inputText.trim() && !hasResults}
          startIcon={<ClearIcon />}
        >
          {t('iocDefanger.inputForm.clear')}
        </Button>
        <Button
          size="small"
          variant="contained"
          onClick={onProcess}
          disabled={!inputText.trim()}
          startIcon={<ProcessIcon />}
        >
          {operation === 'defang' ? t('iocDefanger.inputForm.defangButton') : t('iocDefanger.inputForm.fangButton')}
        </Button>
      </Stack>
    </>
  );
};

export default InputForm;
