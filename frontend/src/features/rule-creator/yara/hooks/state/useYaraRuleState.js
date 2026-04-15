import { useState } from 'react';
import { 
  INITIAL_METADATA, 
  INITIAL_CONDITIONS, 
  INITIAL_STRING 
} from '../../constants/yaraConstants';

/**
 * Custom hook for managing YARA rule state
 * @returns {Object} State and state management functions
 */
export const useYaraRuleState = () => {
  const [metadata, setMetadata] = useState(INITIAL_METADATA);
  const [strings, setStrings] = useState([]);
  const [conditions, setConditions] = useState(INITIAL_CONDITIONS);
  const [currentString, setCurrentString] = useState(INITIAL_STRING);
  const [tags, setTags] = useState([]);
  const [currentTag, setCurrentTag] = useState('');

  // Metadata management
  const updateMetadata = (field, value) => {
    setMetadata(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const resetMetadata = () => {
    setMetadata(INITIAL_METADATA);
  };

  // String management
  const addString = (stringData) => {
    setStrings(prev => [...prev, { id: crypto.randomUUID(), ...stringData }]);
  };

  const removeString = (idToRemove) => {
    setStrings(prev => prev.filter((s) => s.id !== idToRemove));
  };

  const updateCurrentString = (field, value) => {
    setCurrentString(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const resetCurrentString = () => {
    setCurrentString(INITIAL_STRING);
  };

  // Conditions management
  const updateConditions = (field, value) => {
    setConditions(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const setStringMatchCondition = (type) => {
    setConditions(prev => ({
      ...prev,
      all: type === 'all',
      any: type === 'any',
    }));
  };

  const resetConditions = () => {
    setConditions(INITIAL_CONDITIONS);
  };

  // Tag management
  const addTag = (tag) => {
    const trimmedTag = tag.trim();
    if (trimmedTag && !tags.some((t) => t.value === trimmedTag)) {
      setTags(prev => [...prev, { id: crypto.randomUUID(), value: trimmedTag }]);
    }
  };

  const removeTag = (idToRemove) => {
    setTags(prev => prev.filter((tag) => tag.id !== idToRemove));
  };

  const updateCurrentTag = (value) => {
    setCurrentTag(value);
  };

  const resetCurrentTag = () => {
    setCurrentTag('');
  };

  // Complete reset
  const resetAll = () => {
    resetMetadata();
    setStrings([]);
    resetConditions();
    resetCurrentString();
    setTags([]);
    resetCurrentTag();
  };

  return {
    // State
    metadata,
    strings,
    conditions,
    currentString,
    tags,
    currentTag,
    
    // Metadata actions
    updateMetadata,
    resetMetadata,
    
    // String actions
    addString,
    removeString,
    updateCurrentString,
    resetCurrentString,
    
    // Conditions actions
    updateConditions,
    setStringMatchCondition,
    resetConditions,
    
    // Tag actions
    addTag,
    removeTag,
    updateCurrentTag,
    resetCurrentTag,
    
    // Global actions
    resetAll,
  };
};
