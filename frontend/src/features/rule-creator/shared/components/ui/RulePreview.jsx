import React, { useRef } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function RulePreview({ open, onClose, rulePreview, title = "Rule Preview" }) {
  const preRef = useRef(null);

  const handleCopyToClipboard = () => {
    if (preRef.current) {
      const text = preRef.current.innerText;
      navigator.clipboard.writeText(text);
    }
  };

  // Determine language based on rule content
  const getLanguage = () => {
    if (rulePreview.includes('title:') && rulePreview.includes('detection:')) {
      return 'yaml'; // Sigma rule
    } else if (rulePreview.includes('rule ') && rulePreview.includes('strings:')) {
      return 'javascript'; // YARA rule
    } else if (rulePreview.includes('alert ') || rulePreview.includes('drop ') || rulePreview.includes('msg:')) {
      return 'bash'; // Snort/Suricata rule
    }
    return 'text'; // Default
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Box
          ref={preRef}
          component="pre"
          sx={{
            borderRadius: 1,
            overflowX: 'auto',
            fontSize: '0.875rem',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
          }}
        >
          <SyntaxHighlighter language={getLanguage()} style={tomorrow} showLineNumbers={true}>
            {rulePreview}
          </SyntaxHighlighter>
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 1 }}>
        <Tooltip title="Copy to Clipboard">
          <IconButton onClick={handleCopyToClipboard} size="small" aria-label="Copy to clipboard">
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Button onClick={onClose} size="small">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}
