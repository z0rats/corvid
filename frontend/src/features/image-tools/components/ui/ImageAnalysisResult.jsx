import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAtomValue } from 'jotai';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import InfoIcon from '@mui/icons-material/Info';
import PlaceIcon from '@mui/icons-material/Place';
import DataObjectIcon from '@mui/icons-material/DataObject';
import PublicIcon from '@mui/icons-material/Public';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import GppMaybeIcon from '@mui/icons-material/GppMaybe';
import { hasLlmKeyAtom } from '../../../../core/state/atoms';
import ImagePreview from './ImagePreview';
import FileMetadata from './FileMetadata';
import ExifDetails from './ExifDetails';
import GpsMap from './GpsMap';
import ImageStructurePanel from './ImageStructurePanel';
import ImageGeolocationPanel from './ImageGeolocationPanel';
import RemoveMetadataPanel from './RemoveMetadataPanel';
import AnomalyPanel from './AnomalyPanel';

// Scroll-spy, not a tab switcher: every chapter stays mounted and stacked in
// one scrollable document (matches jpegaudit's "one document you scroll, not
// a pile of tools" layout) - the nav just smooth-scrolls to a chapter and
// highlights whichever one the viewport is currently over.
// Top offset matches the app's fixed 56px header (Layout.jsx's AppBar) so the
// "active" band starts right below it, not underneath it.
const ACTIVE_CHAPTER_ROOT_MARGIN = '-56px 0px -70% 0px';

export default function ImageAnalysisResult({ result, previewUrl, file }) {
  const { t } = useTranslation('imageTools');
  const theme = useTheme();
  const isNarrow = useMediaQuery(theme.breakpoints.down('md'));
  const hasLlmKey = useAtomValue(hasLlmKeyAtom);
  const [activeChapter, setActiveChapter] = useState('general');
  const sectionRefs = useRef({});

  const chapters = useMemo(() => {
    if (!result) return [];
    return [
      { id: 'general', label: t('chapters.general'), icon: <InfoIcon fontSize="small" /> },
      { id: 'anomalies', label: t('chapters.anomalies'), icon: <GppMaybeIcon fontSize="small" /> },
      { id: 'exif', label: t('chapters.exif'), icon: <InfoIcon fontSize="small" /> },
      ...(result.gps ? [{ id: 'gps', label: t('chapters.gps'), icon: <PlaceIcon fontSize="small" /> }] : []),
      { id: 'structure', label: t('chapters.structure'), icon: <DataObjectIcon fontSize="small" /> },
      ...(hasLlmKey ? [{ id: 'geolocation', label: t('chapters.geolocation'), icon: <PublicIcon fontSize="small" /> }] : []),
      { id: 'removeMetadata', label: t('chapters.removeMetadata'), icon: <DeleteSweepIcon fontSize="small" /> },
    ];
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result?.gps, hasLlmKey, t]);

  const chapterIds = chapters.map((c) => c.id).join(',');

  useEffect(() => {
    if (!chapterIds) return undefined;

    // IntersectionObserver callbacks only report entries whose state changed
    // *since the last callback* - not the full current state of every observed
    // element - so this has to accumulate into a persistent map and recompute
    // "topmost currently-intersecting" from the whole map each time, rather
    // than reasoning about just the entries in one callback batch.
    const intersectingTops = new Map();

    const recomputeActiveChapter = () => {
      if (intersectingTops.size === 0) return;
      let bestId = null;
      let bestTop = Infinity;
      for (const [id, top] of intersectingTops) {
        if (top < bestTop) {
          bestTop = top;
          bestId = id;
        }
      }
      setActiveChapter(bestId);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const id = entry.target.dataset.chapterId;
          if (entry.isIntersecting) {
            intersectingTops.set(id, entry.boundingClientRect.top);
          } else {
            intersectingTops.delete(id);
          }
        }
        recomputeActiveChapter();
      },
      { rootMargin: ACTIVE_CHAPTER_ROOT_MARGIN, threshold: 0 }
    );

    Object.values(sectionRefs.current).forEach((el) => el && observer.observe(el));

    // The last chapter can never scroll into the "active" band up top if the
    // page isn't taller than one extra viewport below it - so once the user
    // has scrolled to the bottom of the page, just force-activate whichever
    // chapter is last, regardless of what the observer thinks is intersecting.
    const chapterIdList = chapterIds.split(',');
    const handleScroll = () => {
      const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
      if (atBottom) {
        setActiveChapter(chapterIdList[chapterIdList.length - 1]);
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      observer.disconnect();
      window.removeEventListener('scroll', handleScroll);
    };
  }, [chapterIds]);

  if (!result) {
    return null;
  }

  const scrollToChapter = (id) => {
    setActiveChapter(id);
    sectionRefs.current[id]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const renderChapterContent = (id) => {
    switch (id) {
      case 'general':
        return <FileMetadata fileInfo={result.file_info} hashes={result.hashes} phash={result.phash} />;
      case 'anomalies':
        return <AnomalyPanel file={file} />;
      case 'exif':
        return <ExifDetails exif={result.exif} hasThumbnail={result.has_thumbnail} thumbnailBase64={result.thumbnail_base64} />;
      case 'gps':
        return <GpsMap gps={result.gps} />;
      case 'structure':
        return <ImageStructurePanel file={file} format={result.file_info?.format} />;
      case 'geolocation':
        return <ImageGeolocationPanel file={file} />;
      case 'removeMetadata':
        return <RemoveMetadataPanel file={file} />;
      default:
        return null;
    }
  };

  return (
    <Box>
      <ImagePreview previewUrl={previewUrl} fileInfo={result.file_info} />

      {isNarrow && (
        <Tabs
          value={chapters.some((c) => c.id === activeChapter) ? activeChapter : chapters[0]?.id}
          onChange={(_, value) => scrollToChapter(value)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ mb: 2, borderBottom: 1, borderColor: 'divider', position: 'sticky', top: 56, bgcolor: 'background.paper', zIndex: 1 }}
        >
          {chapters.map((chapter) => (
            <Tab key={chapter.id} value={chapter.id} label={chapter.label} />
          ))}
        </Tabs>
      )}

      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
        {!isNarrow && (
          <List
            sx={{
              width: 220, flexShrink: 0, border: '1px solid', borderColor: 'divider', borderRadius: 1, py: 0.5,
              // top clears the app's own fixed 56px header (Layout.jsx's AppBar) plus 16px breathing room -
              // sticking at just 16 would tuck the first nav item behind that header once scrolled.
              position: 'sticky', top: 72,
            }}
          >
            {chapters.map((chapter) => (
              <ListItemButton
                key={chapter.id}
                selected={chapter.id === activeChapter}
                onClick={() => scrollToChapter(chapter.id)}
                sx={{ borderRadius: 1, mx: 0.5, width: 'auto' }}
              >
                <ListItemIcon sx={{ minWidth: 32 }}>{chapter.icon}</ListItemIcon>
                <ListItemText primary={chapter.label} />
              </ListItemButton>
            ))}
          </List>
        )}

        <Box sx={{ flex: 1, minWidth: 0 }}>
          {chapters.map((chapter) => (
            <Box
              key={chapter.id}
              id={`chapter-${chapter.id}`}
              data-chapter-id={chapter.id}
              ref={(el) => { sectionRefs.current[chapter.id] = el; }}
              sx={{
                // Clears the fixed 56px app header so scrollIntoView doesn't land
                // a chapter's heading underneath it.
                scrollMarginTop: 72, mb: 3, p: 2,
                border: '1px solid', borderColor: 'divider', borderRadius: 1,
              }}
            >
              <Typography variant="subtitle1" fontWeight="medium" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                {chapter.icon}
                {chapter.label}
              </Typography>
              {renderChapterContent(chapter.id)}
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
}
