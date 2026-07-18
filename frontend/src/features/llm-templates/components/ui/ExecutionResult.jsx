import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { styled, alpha } from '@mui/material/styles';
import CopyIcon from '@mui/icons-material/ContentCopy';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { PrismAsyncLight as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialOceanic } from 'react-syntax-highlighter/dist/esm/styles/prism';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2.5),
  marginBottom: theme.spacing(2),
  borderRadius: theme.shape.borderRadius * 1.5,
  backgroundColor: theme.palette.background.paper,
}));

const ResultBox = styled(Box)(({ theme }) => ({
  backgroundColor: alpha(theme.palette.background.paper, 0.7),
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(2),
  border: `1px solid ${alpha(theme.palette.divider, 0.8)}`,
  '& h1, & h2, & h3, & h4, & h5, & h6': {
    marginTop: theme.spacing(3),
    marginBottom: theme.spacing(1),
    '&:first-of-type': { marginTop: 0 },
  },
  '& p': {
    marginTop: theme.spacing(0.5),
    marginBottom: theme.spacing(1.5),
  },
  '& ul, & ol': {
    paddingLeft: theme.spacing(3),
    marginTop: theme.spacing(0.5),
    marginBottom: theme.spacing(1.5),
  },
  '& li': {
    marginBottom: theme.spacing(0.5),
  },
  '& table': {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: theme.spacing(1),
    marginBottom: theme.spacing(2),
  },
  '& th, & td': {
    border: `1px solid ${theme.palette.divider}`,
    padding: theme.spacing(1, 1.5),
    textAlign: 'left',
  },
  '& th': {
    fontWeight: 600,
    backgroundColor: alpha(theme.palette.action.hover, 0.5),
  },
  '& blockquote': {
    borderLeft: `3px solid ${theme.palette.divider}`,
    margin: theme.spacing(1.5, 0),
    padding: theme.spacing(0.5, 2),
    color: theme.palette.text.secondary,
  },
  '& hr': {
    border: 'none',
    borderTop: `1px solid ${theme.palette.divider}`,
    margin: theme.spacing(2, 0),
  },
  '& pre': {
    marginTop: theme.spacing(1),
    marginBottom: theme.spacing(1.5),
  },
}));

export default function ExecutionResult({ result, onCopy }) {
  const { t } = useTranslation('llmTemplates');
  if (!result) return null;

  return (
    <StyledPaper elevation={0} sx={{ mt: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6" fontWeight={600}>{t('executionResult.resultHeading')}</Typography>
        <Tooltip title={t('executionResult.copyResultTooltip')}>
          <IconButton onClick={onCopy} aria-label={t('executionResult.copyResultAria')}><CopyIcon fontSize="small" /></IconButton>
        </Tooltip>
      </Box>
      <ResultBox sx={{ border: 0, backgroundColor: 'background.paper' }}>
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
          {result}
        </ReactMarkdown>
      </ResultBox>
    </StyledPaper>
  );
}
