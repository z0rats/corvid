import { useState, useCallback } from 'react';
import { newsfeedApi } from '../../services/api/newsfeedApi';
import { parseAnalysisResult } from '../../utils/iocParser';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ArticleActions');

export function useArticleActions(updateArticle, updateArticleField) {
  const [analyzing, setAnalyzing] = useState({});
  const [updatingTlp, setUpdatingTlp] = useState({});

  const handleAnalyze = useCallback(async (item) => {
    setAnalyzing(prev => ({ ...prev, [item.id]: true }));
    try {
      const response = await newsfeedApi.analyzeArticle(item.id, !!item.analysis_result);
      let analysisResult = parseAnalysisResult(response.analysis_result);
      updateArticle({ ...item, analysis_result: analysisResult });
    } catch (error) {
      logger.error(`Error analyzing article ${item.id}:`, error);
    } finally {
      setAnalyzing(prev => ({ ...prev, [item.id]: false }));
    }
  }, [updateArticle]);

  const handleTlpUpdate = useCallback(async (item, tlp) => {
    setUpdatingTlp(prev => ({ ...prev, [item.id]: true }));
    try {
      await newsfeedApi.updateArticle(item.id, {
        tlp,
        note: item.note || "",
        read: item.read || false,
      });
      updateArticleField(item.id, "tlp", tlp);
    } catch (error) {
      logger.error(`Error updating TLP for article ${item.id}:`, error);
    } finally {
      setUpdatingTlp(prev => ({ ...prev, [item.id]: false }));
    }
  }, [updateArticleField]);

  const handleNoteSave = useCallback(async (articleId, note) => {
    try {
      await newsfeedApi.updateArticle(articleId, { note });
      updateArticleField(articleId, "note", note);
      updateArticleField(articleId, "editNote", false);
    } catch (error) {
      logger.error(`Error saving note for article ${articleId}:`, error);
    }
  }, [updateArticleField]);

  const handleNoteDelete = useCallback(async (articleId) => {
    try {
      await newsfeedApi.updateArticle(articleId, { note: "" });
      updateArticleField(articleId, "note", "");
    } catch (error) {
      logger.error(`Error deleting note for article ${articleId}:`, error);
    }
  }, [updateArticleField]);

  return {
    analyzing,
    updatingTlp,
    handleAnalyze,
    handleTlpUpdate,
    handleNoteSave,
    handleNoteDelete,
  };
}
