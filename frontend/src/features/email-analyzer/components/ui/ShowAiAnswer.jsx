import React, { useMemo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialOceanic } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import Grow from '@mui/material/Grow';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import { useAiAnalysis } from '../../hooks/api/useAiAnalysis';

function stripHtmlTags(html) {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return doc.body.textContent || '';
}

const MAX_AI_INPUT_LENGTH = 30000;

function normalizeEmailBody(input) {
  const raw = Array.isArray(input) ? input.join('\n') : String(input ?? '');
  const cleaned = stripHtmlTags(raw).replace(/\n{3,}/g, '\n\n').trim();
  return cleaned.slice(0, MAX_AI_INPUT_LENGTH);
}

export default function ShowAiAnswer({ input }) {
  const { result, loading, hasLlmKey, analyzeMailBody } = useAiAnalysis();
  const normalizedInput = useMemo(() => normalizeEmailBody(input), [input]);

  if (!hasLlmKey || !normalizedInput) {
    return null;
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <Button
          variant="contained"
          disableElevation
          size="small"
          disabled={loading}
          onClick={() => analyzeMailBody(normalizedInput)}
        >
          Analyze message body with AI
        </Button>
      </Box>

      {loading && <LinearProgress sx={{ mt: 1 }} />}

      {result && (
        <Grow in>
          <Card
            variant="outlined"
            sx={{
              mt: 2,
              p: 2,
              textAlign: 'left',
              '& h1, & h2, & h3, & h4, & h5, & h6': {
                mt: 3,
                mb: 1,
                '&:first-of-type': { mt: 0 },
              },
              '& p': {
                mt: 0.5,
                mb: 1.5,
              },
              '& ul, & ol': {
                pl: 3,
                mt: 0.5,
                mb: 1.5,
              },
              '& li': {
                mb: 0.5,
              },
              '& table': {
                width: '100%',
                borderCollapse: 'collapse',
                mt: 1,
                mb: 2,
              },
              '& th, & td': {
                border: '1px solid',
                borderColor: 'divider',
                px: 1.5,
                py: 1,
                textAlign: 'left',
              },
              '& th': {
                fontWeight: 600,
                bgcolor: 'action.hover',
              },
              '& blockquote': {
                borderLeft: '3px solid',
                borderColor: 'divider',
                my: 1.5,
                px: 2,
                py: 0.5,
                color: 'text.secondary',
              },
              '& hr': {
                border: 'none',
                borderTop: '1px solid',
                borderColor: 'divider',
                my: 2,
              },
              '& pre': {
                mt: 1,
                mb: 1.5,
              },
            }}
          >
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              AI message-body analysis
            </Typography>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...rest }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={materialOceanic}
                      language={match[1]}
                      PreTag="div"
                      {...rest}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...rest}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {result.toString()}
            </ReactMarkdown>
          </Card>
        </Grow>
      )}
    </Box>
  );
}
