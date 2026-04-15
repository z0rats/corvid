import React, { useState, useRef, useCallback } from "react";
import { useTheme } from '@mui/material/styles';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import ConfirmDeleteDialog from "../../../core/components/ui/ConfirmDeleteDialog";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import EditNoteIcon from "@mui/icons-material/EditNote";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialOceanic } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { MDXEditor, headingsPlugin, listsPlugin, quotePlugin, thematicBreakPlugin, markdownShortcutPlugin, codeBlockPlugin, codeMirrorPlugin, toolbarPlugin, BoldItalicUnderlineToggles, StrikeThroughSupSubToggles, ListsToggle, BlockTypeSelect, InsertThematicBreak, InsertCodeBlock } from '@mdxeditor/editor';
import '@mdxeditor/editor/style.css';

export default function NotesSection({
  item,
  updateArticleField,
  onNoteSave,
  onNoteDelete,
  icon,
  isButton = false,
}) {
  const theme = useTheme();
  const editorRef = useRef(null);
  const [noteContent, setNoteContent] = useState(item.note || "");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const handleEditorChange = useCallback((markdown) => {
    setNoteContent(markdown);
  }, []);

  const handleNoteEdit = () => {
    updateArticleField(item.id, "editNote", true);
  };

  const handleNoteSave = async () => {
    if (onNoteSave) {
      await onNoteSave(item.id, noteContent);
    }
  };

  const handleCancel = () => {
    setNoteContent(item.note || "");
    updateArticleField(item.id, "editNote", false);
  };

  const handleDeleteConfirm = async () => {
    if (onNoteDelete) {
      await onNoteDelete(item.id);
    }
    setNoteContent("");
    setDeleteDialogOpen(false);
  };

  if (isButton) {
    return (
      <Tooltip title="Add or Edit Note" arrow>
        <IconButton onClick={handleNoteEdit} sx={{ color: "primary.main" }} aria-label={item.note ? "Edit Note" : "Add Note"}>
          {icon}
        </IconButton>
      </Tooltip>
    );
  }

  return (
    <>
      <Accordion sx={{ borderRadius: 1 }} variant="secondary" defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ flexDirection: "row-reverse", alignItems: "center" }}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <EditNoteIcon />
            <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
              Note:
            </Typography>
          </Stack>
          <Box sx={{ flexGrow: 1 }} />
          <Stack direction="row" spacing={0.5} sx={{ mr: 1 }}>
            {!item.editNote && (
              <Tooltip title="Edit Note" arrow>
                <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleNoteEdit(); }} aria-label="Edit Note">
                  <EditIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            <Tooltip title="Delete Note" arrow>
              <IconButton
                size="small"
                onClick={(e) => { e.stopPropagation(); setDeleteDialogOpen(true); }}
                aria-label="Delete Note"
                sx={{ "&:hover": { color: "error.main" } }}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        </AccordionSummary>
        <AccordionDetails>
          {item.editNote ? (
            <Stack direction="column" spacing={1}>
              <Box className="mdxeditor-wrapper" sx={{ height: 150, minHeight: 60, resize: 'vertical', overflow: 'auto', border: 1, borderColor: 'divider', borderRadius: 1 }}>
                <MDXEditor
                  ref={editorRef}
                  className={theme.palette.mode === 'dark' ? 'dark-theme' : ''}
                  markdown={noteContent}
                  onChange={handleEditorChange}
                  plugins={[
                    headingsPlugin(),
                    listsPlugin(),
                    quotePlugin(),
                    thematicBreakPlugin(),
                    markdownShortcutPlugin(),
                    codeBlockPlugin(),
                    codeMirrorPlugin({ codeBlockLanguages: { '': 'Plain Text', js: 'JavaScript', python: 'Python', css: 'CSS', html: 'HTML', json: 'JSON', bash: 'Bash', text: 'Plain Text' } }),
                    toolbarPlugin({ toolbarContents: () => (<><BlockTypeSelect /><BoldItalicUnderlineToggles /><StrikeThroughSupSubToggles /><ListsToggle /><InsertCodeBlock /><InsertThematicBreak /></>) }),
                  ]}
                />
              </Box>
              <Stack direction="row" spacing={1}>
                <Button variant="contained" disableElevation onClick={handleNoteSave}>
                  Save Note
                </Button>
                <Button variant="outlined" disableElevation onClick={handleCancel}>
                  Cancel
                </Button>
              </Stack>
            </Stack>
          ) : (
            <Box sx={{
              mt: 1,
              '& ul, & ol': { paddingLeft: 3, marginY: 0.5 },
              '& li': { marginBottom: 0.5 },
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
                {item.note}
              </ReactMarkdown>
            </Box>
          )}
        </AccordionDetails>
      </Accordion>

      <ConfirmDeleteDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Note"
        message="Are you sure you want to delete this note? This action cannot be undone."
      />
    </>
  );
}
