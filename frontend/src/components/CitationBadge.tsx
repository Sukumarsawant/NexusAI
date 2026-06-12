import React, { useState } from 'react';
import { FileText, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { CitationItem } from '../types';

interface CitationBadgeProps {
  citation: CitationItem;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="inline-block my-1 mr-2 text-xs">
      <button
        onClick={() => setExpanded(!expanded)}
        className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 hover:bg-brand-50 hover:text-brand-700 dark:hover:bg-brand-950 dark:hover:text-brand-300 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition"
      >
        <FileText className="h-3 w-3 text-brand-500" />
        <span className="font-medium">
          Source {citation.source_id}: {citation.filename}
        </span>
        {citation.page_or_row && (
          <span className="text-slate-400 dark:text-slate-500">
            • {citation.page_or_row}
          </span>
        )}
        <span className="px-1.5 py-0.2 rounded bg-slate-200 dark:bg-slate-700 font-mono text-[10px]">
          {(citation.relevance_score * 100).toFixed(0)}%
        </span>
        {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>

      {expanded && (
        <div className="mt-1 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs shadow-sm max-w-lg">
          <div className="font-semibold text-slate-800 dark:text-slate-200 mb-1 flex items-center justify-between">
            <span>Excerpt Reference</span>
            <span className="text-[10px] text-slate-400">Chunk #{citation.chunk_index}</span>
          </div>
          <p className="italic text-slate-600 dark:text-slate-400 font-serif leading-relaxed">
            "{citation.snippet}"
          </p>
        </div>
      )}
    </div>
  );
};
