import { useState } from 'react';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Collapse from '@mui/material/Collapse';
import Typography from '@mui/material/Typography';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDownOutlined';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUpOutlined';

/**
 * Collapsible dump of a source's verbatim scraped payload (HTML/JSON as received),
 * so the analyst can always verify what a source actually returned - not just what the
 * parser extracted from it. Styled after ioc-tools' ServiceResultRow raw-JSON fallback,
 * but standalone rather than table-row-embedded since it's reused for both ЕГРЮЛ and
 * РДЛ payloads here.
 */
export default function RawResponsePanel({ label, raw }) {
  const [open, setOpen] = useState(false);

  if (!raw) return null;

  return (
    <Box sx={{ mt: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, cursor: 'pointer' }} onClick={() => setOpen((prev) => !prev)}>
        <IconButton size="small" aria-label="Показать сырые данные">
          {open ? <KeyboardArrowUpIcon fontSize="small" /> : <KeyboardArrowDownIcon fontSize="small" />}
        </IconButton>
        <Typography variant="caption" color="text.secondary">{label}</Typography>
      </Box>
      <Collapse in={open} timeout="auto" unmountOnExit>
        <Box
          component="pre"
          sx={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
            fontSize: '12px',
            backgroundColor: 'background.paper',
            p: 1.25,
            mt: 0.5,
            borderRadius: 0.5,
            border: 1,
            borderColor: 'divider',
            maxHeight: '400px',
            overflowY: 'auto',
          }}
        >
          {raw}
        </Box>
      </Collapse>
    </Box>
  );
}
