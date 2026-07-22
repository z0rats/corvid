import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Box from '@mui/material/Box';
import { useTranslation } from 'react-i18next';

const SHORTCUTS = [
  ['/  ⌘K', 'openPalette'],
  ['↑ / ↓', 'navigate'],
  ['Enter', 'openRun'],
  ['⌘1-9', 'jumpToResult'],
  ['Tab', 'complete'],
  ['⌘V', 'pasteImage'],
  ['⌘K', 'actionPanel'],
  ['⌘C', 'copy'],
  ['⌥⌘C', 'copyDefanged'],
  ['⌘⇧B', 'addToBulk'],
  ['⌘P', 'pin'],
  ['⌘↑ / ⌘↓', 'queryHistory'],
  ['Esc', 'clearOrClose'],
  ['?', 'shortcuts'],
  ['⌘,', 'settings'],
];

export default function ShortcutSheet({ open, onClose }) {
  const { t } = useTranslation('commandPalette');

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>{t('shortcuts.title')}</DialogTitle>
      <DialogContent>
        <Table size="small">
          <TableBody>
            {SHORTCUTS.map(([keys, labelKey]) => (
              <TableRow key={labelKey}>
                <TableCell sx={{ fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                  <Box component="span">{keys}</Box>
                </TableCell>
                <TableCell>{t(`shortcuts.${labelKey}`)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </DialogContent>
    </Dialog>
  );
}
