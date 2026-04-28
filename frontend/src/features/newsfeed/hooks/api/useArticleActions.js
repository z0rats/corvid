import { useState, useCallback } from 'react';
import { newsfeedApi } from '../../services/api/newsfeedApi';
import { parseAnalysisResult } from '../../utils/iocParser';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ArticleActions');

export function useArticleActions(updateArticle, updateArticleField) {
  const [analyzing, setAnalyzing] = useState({});
  const [updatingTlp, setUpdatingTlp] = useState({});

  const handleAnalyze = useCallback(async (item, mode = "all") => {
    setAnalyzing(prev => ({ ...prev, [item.id]: true }));
    try {
      const hasExisting = mode === "all" ? !!(item.analysis_result || item.mitre_attack)
        : mode === "analysis" ? !!item.analysis_result
        : !!item.mitre_attack;
      const response = await newsfeedApi.analyzeArticle(item.id, hasExisting, mode);
      const updates = { ...item };
      if (response.analysis_result) updates.analysis_result = parseAnalysisResult(response.analysis_result);
      if (response.mitre_attack !== undefined) updates.mitre_attack = response.mitre_attack || null;
      updateArticle(updates);
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
