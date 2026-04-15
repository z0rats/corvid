import React, { useState } from "react";
import { useAtomValue } from "jotai";
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CircularProgress from '@mui/material/CircularProgress';
import Grow from '@mui/material/Grow';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CircleIcon from '@mui/icons-material/Circle';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import RateReviewIcon from '@mui/icons-material/RateReview';
import { format } from "date-fns";
import he from "he";

import { hasLlmKeyAtom } from "../../../core/state/atoms";
import { getFeedIconUrl } from "../utils/urlUtils";
import AnalyzeSection from "./AnalyzeSection";
import NotesSection from "./NotesSection";
import IOCSection from "./IOCSection";
import KeywordsSection from "./KeywordsSection";

const isValidUrl = (url) => /^https?:\/\//i.test(url);

const NewsArticleItem = React.memo(function NewsArticleItem({
  item,
  updateArticle,
  updateArticleField,
  tlpColors,
  onAnalyze,
  onTlpUpdate,
  onNoteSave,
  onNoteDelete,
  analyzing,
  updatingTlp,
}) {
  const hasLlmKey = useAtomValue(hasLlmKeyAtom);
  const [tlpAnchorEl, setTlpAnchorEl] = useState(null);

  const handleTlpSelect = async (tlp) => {
    setTlpAnchorEl(null);
    if (onTlpUpdate) {
      await onTlpUpdate(item, tlp);
    }
  };

  return (
    <Grow in={true} key={`grow-${item.id}`}>
      <Card
        sx={{
          mb: 2,
          p: 2,
          borderRadius: 1,
          boxShadow: 0,
          borderLeft: item.tlp !== "TLP:CLEAR" ? 5 : 0,
          borderLeftColor: tlpColors[item.tlp || "TLP:CLEAR"],
        }}
      >
        <Stack direction="row" spacing={1} sx={{ mb: 1 }} justifyContent="space-between" alignItems="center">
          <Stack direction="row" spacing={1} alignItems="center">
            <Avatar
              alt={`${item.title} icon`}
              src={getFeedIconUrl(item.icon)}
              sx={{ width: 45, height: 45 }}
              variant="rounded"
            />
            <Stack>
              <Typography variant="subtitle1">
                <b>{item.feedname}</b>
              </Typography>
              <Typography variant="body2">
                {format(new Date(item.date), "MMMM d, yyyy, h:mm a")}
              </Typography>
            </Stack>
          </Stack>

          <Stack direction="row" spacing={1} alignItems="center">
            <Tooltip title="Change TLP" arrow>
              <span>
                <IconButton
                  onClick={(e) => setTlpAnchorEl(e.currentTarget)}
                  sx={{ color: tlpColors[item.tlp || "CLEAR"] }}
                  aria-label="Change TLP Level"
                  disabled={updatingTlp}
                >
                  {updatingTlp ? <CircularProgress size={24} color="inherit" /> : <CircleIcon />}
                </IconButton>
              </span>
            </Tooltip>
            <Menu anchorEl={tlpAnchorEl} open={Boolean(tlpAnchorEl)} onClose={() => setTlpAnchorEl(null)}>
              {Object.entries(tlpColors).map(([tlp, color]) => (
                <MenuItem key={tlp} onClick={() => handleTlpSelect(tlp)} sx={{ color }}>
                  {tlp}
                </MenuItem>
              ))}
            </Menu>

            <NotesSection
              item={item}
              updateArticleField={updateArticleField}
              onNoteSave={onNoteSave}
              onNoteDelete={onNoteDelete}
              icon={<RateReviewIcon />}
              isButton
            />

            <Tooltip title={"View Original Article on " + item.feedname} arrow>
              {isValidUrl(item.link) ? (
                <Button
                  sx={{ borderRadius: 5 }}
                  disableElevation
                  startIcon={<OpenInNewIcon />}
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Open Original Article"
                >
                  Original
                </Button>
              ) : (
                <span>
                  <Button
                    sx={{ borderRadius: 5 }}
                    disableElevation
                    startIcon={<OpenInNewIcon />}
                    disabled
                    aria-label="Invalid article URL"
                  >
                    Original
                  </Button>
                </span>
              )}
            </Tooltip>

            {hasLlmKey && (
              <Tooltip title="Analyze Article Using AI" arrow>
                <span>
                  <Button
                    sx={{ borderRadius: 5 }}
                    disableElevation
                    startIcon={<AutoAwesomeIcon />}
                    onClick={() => onAnalyze && onAnalyze(item)}
                    disabled={analyzing}
                    aria-label="Analyze Article"
                  >
                    {analyzing ? (
                      <>
                        Analyzing...
                        <CircularProgress size={20} sx={{ ml: 1 }} color="inherit" />
                      </>
                    ) : item.analysis_result ? (
                      "Re-analyze"
                    ) : (
                      "Analyze"
                    )}
                  </Button>
                </span>
              </Tooltip>
            )}
          </Stack>
        </Stack>

        <Typography variant="h6" sx={{ mb: 1 }}>
          {item.title}
        </Typography>
        <Typography sx={{ mb: 2 }}>
          {item.summary ? he.decode(item.summary) : "No summary available for this article."}
        </Typography>

        {item.analysis_result && <AnalyzeSection item={item} />}

        {(item.note || item.editNote) && (
          <NotesSection
            item={item}
            updateArticleField={updateArticleField}
            onNoteSave={onNoteSave}
            onNoteDelete={onNoteDelete}
          />
        )}

        <Box>
          <IOCSection item={item} />
          <KeywordsSection item={item} />
        </Box>
      </Card>
    </Grow>
  );
});

export default NewsArticleItem;
