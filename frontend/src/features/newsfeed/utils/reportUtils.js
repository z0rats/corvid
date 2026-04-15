export function generateMarkdown(ranking, analysisResults) {
  let md = `# Newsfeed Analysis Report\n\n`;
  md += `**Analysis Date:** ${new Date().toLocaleString()}\n\n`;

  md += `## Top Ranked Articles\n\n`;
  if (ranking.length === 0) {
    md += `_No articles were ranked._\n\n`;
  } else {
    ranking.forEach((article, index) => {
      md += `**${index + 1}. ${article.title}**\n\n`;
      md += `- **Reason**: ${article.reason}\n\n`;
    });
  }

  md += `## Detailed Analysis\n\n`;
  if (analysisResults.length === 0) {
    md += `_No detailed analysis yet._\n\n`;
  } else {
    analysisResults.forEach((res, i) => {
      const { title, analysis } = res;
      md += `### ${i + 1}. ${title}\n\n`;
      md += `- **Risk**: ${analysis.Risk}\n`;
      md += `- **Summary**: ${analysis.Summary}\n`;
      md += `- **Comment**: ${analysis['Analysis comment']}\n`;
      md += `- **Possible Action Items**:\n`;
      (analysis['Action items'] || []).forEach((item) => {
        md += `  - ${item}\n`;
      });
      md += `- **Source**: ${analysis['Source']}\n\n`;
    });
  }

  return md;
}

export function downloadMarkdown(markdownContent, filename = 'analysis_report.md') {
  const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
