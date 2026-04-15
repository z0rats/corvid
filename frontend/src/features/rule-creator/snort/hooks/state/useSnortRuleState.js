import { useState } from 'react';
import {
  createInitialRuleHeader,
  createInitialRuleOptions,
  createInitialRuleContent,
  createInitialRuleMetadata,
} from '../../services/snortRuleService';

export const useSnortRuleState = () => {
  const [ruleHeader, setRuleHeader] = useState(createInitialRuleHeader);
  const [ruleOptions, setRuleOptions] = useState(createInitialRuleOptions);
  const [ruleContent, setRuleContent] = useState(createInitialRuleContent);
  const [ruleMetadata, setRuleMetadata] = useState(createInitialRuleMetadata);

  const resetAll = () => {
    setRuleHeader(createInitialRuleHeader());
    setRuleOptions(createInitialRuleOptions());
    setRuleContent(createInitialRuleContent());
    setRuleMetadata(createInitialRuleMetadata());
  };

  return {
    ruleHeader,
    ruleOptions,
    ruleContent,
    ruleMetadata,

    setRuleHeader,
    setRuleOptions,
    setRuleContent,
    setRuleMetadata,

    resetAll,
  };
};
