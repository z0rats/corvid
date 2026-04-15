import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import ClearIcon from '@mui/icons-material/Clear';
import CopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import ProcessIcon from '@mui/icons-material/PlayArrow';

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
  const lineCount = inputText.split('\n').filter(line => line.trim()).length;

  return (
    <>
      <TextField
        fullWidth
        multiline
        minRows={8}
        variant="outlined"
        sx={{ '& .MuiInputBase-inputMultiline': { resize: 'vertical' } }}
        label={`Enter IOCs to ${operation} (one per line)`}
        placeholder={operation === 'defang'
          ? "https://example.com\n192.168.1.1\nuser@domain.com\nmalware.exe"
          : "hxxps[://]example[.]com\n192[.]168[.]1[.]1\nuser[@]domain[.]com"
        }
        value={inputText}
        onChange={(e) => onInputChange(e.target.value)}
        helperText={`Supports domains, IPs, URLs, emails, filenames. ${lineCount} lines entered.`}
      />

      <Stack direction="row" spacing={1} sx={{ mt: 1.5, justifyContent: 'flex-start' }}>
        {hasResults && (
          <Button
            size="small"
            variant="outlined"
            onClick={onCopyAllResults}
            startIcon={<CopyIcon />}
          >
            Copy All Results
          </Button>
        )}
        {hasResults && (
          <Button
            size="small"
            variant="outlined"
            onClick={onDownloadCsv}
            startIcon={<DownloadIcon />}
          >
            Download CSV
          </Button>
        )}
        <Button
          size="small"
          variant="outlined"
          onClick={onClear}
          disabled={!inputText.trim() && !hasResults}
          startIcon={<ClearIcon />}
        >
          Clear
        </Button>
        <Button
          size="small"
          variant="contained"
          onClick={onProcess}
          disabled={!inputText.trim()}
          startIcon={<ProcessIcon />}
        >
          {operation === 'defang' ? 'Defang' : 'Fang'}
        </Button>
      </Stack>
    </>
  );
};

export default InputForm;
