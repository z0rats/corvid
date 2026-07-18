import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import CodeIcon from '@mui/icons-material/Code';
import PersonIcon from '@mui/icons-material/Person';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import ThermostatIcon from '@mui/icons-material/Thermostat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { PrismAsyncLight as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialOceanic } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function TemplateExampleDialog({ open, onClose, template }) {
  const { t } = useTranslation('llmTemplates');
  if (!template) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ pb: 1 }}>
        <Typography variant="h6">{template.title}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          {template.description}
        </Typography>
        <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
          <Chip icon={<CodeIcon fontSize="small" />} label={template.model} size="small" variant="outlined" />
          <Chip icon={<ThermostatIcon fontSize="small" />} label={t('exampleDialog.temperatureLabel', { value: template.temperature?.toFixed(2) })} size="small" variant="outlined" />
        </Stack>
      </DialogTitle>
      <DialogContent sx={{ pt: 2 }}>
        <Stack spacing={2}>
          <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            <Stack direction="row" alignItems="center" spacing={1} mb={1}>
              <PersonIcon fontSize="small" color="primary" />
              <Typography variant="subtitle2" color="primary">{t('exampleDialog.agentRole')}</Typography>
            </Stack>
            <Typography variant="body2">{template.ai_agent_role}</Typography>
          </Paper>

          <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            <Stack direction="row" alignItems="center" spacing={1} mb={1}>
              <TaskAltIcon fontSize="small" color="primary" />
              <Typography variant="subtitle2" color="primary">{t('exampleDialog.agentTask')}</Typography>
            </Stack>
            <Typography variant="body2">{template.ai_agent_task}</Typography>
          </Paper>

          <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            <Typography variant="subtitle2" color="primary" mb={1}>{t('exampleDialog.example')}</Typography>
            <Box sx={{
              '& > *:first-of-type': { mt: 0 },
              '& > *:last-child': { mb: 0 },
              '& ul, & ol': { pl: 3 },
              '& p': { my: 1 },
            }}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...rest }) {
                    const match = /language-(\w+)/.exec(className || '');
                    if (!inline) {
                      return (
                        <SyntaxHighlighter style={materialOceanic} language={match ? match[1] : 'text'} PreTag="div" {...rest}>
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      );
                    }
                    return <code className={className} {...rest}>{children}</code>;
                  },
                }}
              >
                {template.example_input_output || t('exampleDialog.noExample')}
              </ReactMarkdown>
            </Box>
          </Paper>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('exampleDialog.closeButton')}</Button>
      </DialogActions>
    </Dialog>
  );
}
