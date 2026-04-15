import { useState } from 'react';
import { 
  createInitialMetadata, 
  createInitialLogSource, 
  createInitialDetection 
} from '../../services/sigmaRuleService';
/**
 * Custom hook for managing Sigma rule state
 * @returns {Object} State and state management functions
 */
export const useSigmaRuleState = () => {
  const [metadata, setMetadata] = useState(createInitialMetadata);
  const [logSource, setLogSource] = useState(createInitialLogSource);
  const [detections, setDetections] = useState(createInitialDetection);
  const [conditionsList, setConditionsList] = useState([]);
  const [fields, setFields] = useState([]);
  const [references, setReferences] = useState([]);
  const [tags, setTags] = useState([]);
  const [falsePositives, setFalsePositives] = useState([]);

  // Reset all state to initial values
  const resetAll = () => {
    setMetadata(createInitialMetadata());
    setLogSource(createInitialLogSource());
    setDetections(createInitialDetection());
    setConditionsList([]);
    setFields([]);
    setReferences([]);
    setTags([]);
    setFalsePositives([]);
  };

  return {
    // State
    metadata,
    logSource,
    detections,
    conditionsList,
    fields,
    references,
    tags,
    falsePositives,
    
    // State setters
    setMetadata,
    setLogSource,
    setDetections,
    setConditionsList,
    setFields,
    setReferences,
    setTags,
    setFalsePositives,
    
    // Actions
    resetAll,
  };
};
