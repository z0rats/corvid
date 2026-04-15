import React from 'react';
import GeneralInfo from './GeneralInfo';
import SecurityCheck from './SecurityCheck';
import Attachments from './Attachments';
import Urls from './Urls';
import Hops from './Hops';
import Header from './Header';
import MessageBody from './MessageBody';

export default function EmailAnalysisResult({ result }) {
  if (!result) {
    return null;
  }

  return (
    <>
      <GeneralInfo
        result={result["basic_info"]}
        hashes={result["eml_hashes"]}
      />

      <SecurityCheck result={result["warnings"]} />

      <Attachments result={result["attachments"]} />

      <Urls result={result["urls"]} />

      <Hops result={result["hops"]} />

      <Header result={result["headers"]} />

      <MessageBody result={result["message_text"]} />
    </>
  );
}
