import React, { useRef, useState } from "react";
import { useAtomValue } from "jotai";
import { useTranslation } from "react-i18next";
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import Card from '@mui/material/Card';
import CircularProgress from '@mui/material/CircularProgress';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import Grow from '@mui/material/Grow';
import IconButton from '@mui/material/IconButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import MenuList from '@mui/material/MenuList';
import Paper from '@mui/material/Paper';
import Popper from '@mui/material/Popper';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CircleIcon from '@mui/icons-material/Circle';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import RateReviewIcon from '@mui/icons-material/RateReview';
import ShieldIcon from '@mui/icons-material/Shield';
import { format } from "date-fns";

import { hasLlmKeyAtom } from "../../../core/state/atoms";
import { getFeedIconUrl } from "../utils/urlUtils";
import AnalyzeSection from "./AnalyzeSection";
import MitreAttackSection from "./MitreAttackSection";
import NotesSection from "./NotesSection";
import IOCSection from "./IOCSection";
import KeywordsSection from "./KeywordsSection";

const isValidUrl = (url) => /^https?:\/\//i.test(url);

const decodeHtmlEntities = (str) => {
  const el = document.createElement("textarea");
  el.innerHTML = str;
  return el.value;
};

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
  const { t } = useTranslation('newsfeed');
  const hasLlmKey = useAtomValue(hasLlmKeyAtom);
  const [tlpAnchorEl, setTlpAnchorEl] = useState(null);
  const [analyzeOpen, setAnalyzeOpen] = useState(false);
  const analyzeRef = useRef(null);

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
            <Tooltip title={t('feed.article.changeTlp')} arrow>
              <span>
                <IconButton
                  onClick={(e) => setTlpAnchorEl(e.currentTarget)}
                  sx={{ color: tlpColors[item.tlp || "CLEAR"] }}
                  aria-label={t('feed.article.changeTlpLevel')}
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

            <Tooltip title={t('feed.article.viewOriginalOn', { feedName: item.feedname })} arrow>
              {isValidUrl(item.link) ? (
                <Button
                  disableElevation
                  size="small"
                  startIcon={<OpenInNewIcon />}
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={t('feed.article.openOriginalArticle')}
                >
                  {t('feed.article.original')}
                </Button>
              ) : (
                <span>
                  <Button
                    disableElevation
                    size="small"
                    startIcon={<OpenInNewIcon />}
                    disabled
                    aria-label={t('feed.article.invalidArticleUrl')}
                  >
                    {t('feed.article.original')}
                  </Button>
                </span>
              )}
            </Tooltip>

            {hasLlmKey && (
              <>
                <Tooltip title={analyzeOpen ? "" : t('feed.article.analyzeUsingAi')} arrow>
                  <ButtonGroup variant="text" disableElevation ref={analyzeRef} size="small">
                    <Button
                      startIcon={<AutoAwesomeIcon />}
                      onClick={() => onAnalyze && onAnalyze(item, "all")}
                      disabled={analyzing}
                    >
                      {analyzing ? (
                        <>
                          {t('feed.article.analyzing')}
                          <CircularProgress size={16} sx={{ ml: 1 }} color="inherit" />
                        </>
                      ) : (item.analysis_result || item.mitre_attack) ? (
                        t('feed.article.reanalyze')
                      ) : (
                        t('feed.article.analyze')
                      )}
                    </Button>
                    <Button
                      size="small"
                      onClick={() => setAnalyzeOpen((prev) => !prev)}
                      disabled={analyzing}
                    >
                      <ArrowDropDownIcon />
                    </Button>
                  </ButtonGroup>
                </Tooltip>
                <Popper sx={{ zIndex: 1 }} open={analyzeOpen} anchorEl={analyzeRef.current} placement="bottom-end">
                  <Grow in={analyzeOpen}>
                    <Paper>
                      <ClickAwayListener onClickAway={() => setAnalyzeOpen(false)}>
                        <MenuList>
                          <MenuItem onClick={() => { setAnalyzeOpen(false); onAnalyze && onAnalyze(item, "analysis"); }}>
                            <ListItemIcon><AutoAwesomeIcon fontSize="small" /></ListItemIcon>
                            <ListItemText>{t('feed.article.aiAnalysisMenuItem')}</ListItemText>
                          </MenuItem>
                          <MenuItem onClick={() => { setAnalyzeOpen(false); onAnalyze && onAnalyze(item, "mitre"); }}>
                            <ListItemIcon><ShieldIcon fontSize="small" /></ListItemIcon>
                            <ListItemText>{t('feed.article.mitreMappingMenuItem')}</ListItemText>
                          </MenuItem>
                        </MenuList>
                      </ClickAwayListener>
                    </Paper>
                  </Grow>
                </Popper>
              </>
            )}
          </Stack>
        </Stack>

        <Typography variant="h6" sx={{ mb: 1 }}>
          {item.title}
        </Typography>
        <Typography sx={{ mb: 2 }}>
          {item.summary ? decodeHtmlEntities(item.summary) : t('feed.noSummary')}
        </Typography>

        {item.analysis_result && <AnalyzeSection item={item} />}
        {item.mitre_attack && <MitreAttackSection item={item} />}

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
