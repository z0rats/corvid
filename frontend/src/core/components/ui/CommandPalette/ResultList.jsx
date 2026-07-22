import List from '@mui/material/List';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';
import ResultRow from './ResultRow';

export default function ResultList({ results, selectedIndex, onSelect, onActionPanel }) {
  const { t } = useTranslation('commandPalette');

  if (results.length === 0) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">{t('results.empty')}</Typography>
      </Box>
    );
  }

  return (
    <List disablePadding sx={{ maxHeight: 360, overflowY: 'auto' }}>
      {results.map((item, index) => (
        <ResultRow
          key={item.type === 'entry' ? item.entry.id : `${item.type}-${item.value}-${index}`}
          item={item}
          index={index}
          isSelected={index === selectedIndex}
          onSelect={onSelect}
          onActionPanel={onActionPanel}
        />
      ))}
    </List>
  );
}
