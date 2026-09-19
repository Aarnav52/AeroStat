import React, { useState, useEffect } from 'react';
import {
  Sparkles, Send, Loader2, AlertCircle, ChevronDown, ChevronRight,
  Lightbulb, ShieldAlert, Wrench, X,
} from 'lucide-react';
import { postAnalystQuery } from '../api/apiService';

// ─── Small helpers ─────────────────────────────────────────────────────────────

function EvidenceToggle({ toolCalls }) {
  const [open, setOpen] = useState(false);
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div className="pt-3 border-t border-slate-800/70">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-[11px] font-bold text-slate-400 hover:text-sky-400 transition-all uppercase tracking-wider"
      >
        {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        <Wrench className="w-3 h-3" />
        {toolCalls.length} tool call{toolCalls.length === 1 ? '' : 's'} used
      </button>

      {open && (
        <div className="mt-3 space-y-2">
          {toolCalls.map((call, i) => (
            <div key={i} className="p-3 rounded-xl glass-soft text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-sky-300">{call.tool_name}</span>
              </div>
              {call.arguments && Object.keys(call.arguments).length > 0 && (
                <div className="text-slate-400">
                  <span className="text-slate-500">args: </span>
                  <span className="font-mono">{JSON.stringify(call.arguments)}</span>
                </div>
              )}
              <pre className="text-slate-400 font-mono text-[11px] whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                {JSON.stringify(call.result, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AnswerCard({ entry }) {
  const { question, response, error } = entry;

  return (
    <div className="glass-elevated p-5 rounded-2xl space-y-4">
      <div className="flex items-start gap-2">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider shrink-0 mt-0.5">Q</span>
        <p className="text-sm font-semibold text-slate-200">{question}</p>
      </div>

      {error ? (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-start gap-2">
            <span className="text-[11px] font-bold text-sky-400 uppercase tracking-wider shrink-0 mt-0.5">A</span>
            <p className="text-sm text-slate-100 leading-relaxed whitespace-pre-wrap">{response.answer}</p>
          </div>

          {response.key_findings?.length > 0 && (
            <div className="pl-1">
              <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                <Lightbulb className="w-3 h-3" /> Key Findings
              </div>
              <ul className="space-y-1 list-disc list-inside text-xs text-slate-300">
                {response.key_findings.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}

          {response.limitations?.length > 0 && (
            <div className="pl-1">
              <div className="flex items-center gap-1.5 text-[11px] font-bold text-amber-400 uppercase tracking-wider mb-1.5">
                <ShieldAlert className="w-3 h-3" /> Limitations
              </div>
              <ul className="space-y-1 list-disc list-inside text-xs text-amber-200/80">
                {response.limitations.map((l, i) => <li key={i}>{l}</li>)}
              </ul>
            </div>
          )}

          <EvidenceToggle toolCalls={response.tool_calls} />
        </div>
      )}
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────────
// Renders as a modal popup (backdrop + centered panel), reachable from any
// tab in the app rather than being a tab of its own - see App.jsx.

export default function AnalystChat({ onClose }) {
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState([]); // newest first: [{id, question, response?, error?}]
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setQuestion('');
    const id = Date.now();

    try {
      const response = await postAnalystQuery(trimmed);
      setHistory((h) => [{ id, question: trimmed, response }, ...h]);
    } catch (err) {
      setHistory((h) => [{ id, question: trimmed, error: err.message || 'Request failed' }, ...h]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start sm:items-center justify-center bg-slate-950/70 backdrop-blur-sm p-4 sm:p-6"
      onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}
    >
      <div className="w-full max-w-3xl max-h-[85vh] flex flex-col glass-elevated rounded-2xl border border-slate-800 shadow-2xl mt-8 sm:mt-0 overflow-hidden">

        <div className="flex items-start justify-between gap-3 p-5 border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl glass-soft flex items-center justify-center text-sky-400 shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-white font-sans tracking-tight">
                AeroStat Analyst
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Every number comes from a deterministic tool call against the live database.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all shrink-0"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 shrink-0">
          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. How has the DEL-BOM index changed this week?"
              disabled={loading}
              autoFocus
              className="flex-grow px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="flex items-center gap-1.5 px-4 py-3 text-xs font-bold rounded-xl text-white bg-sky-600 hover:bg-sky-500 border border-sky-500 transition-all disabled:opacity-50 shadow-md shrink-0"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {loading ? 'Thinking…' : 'Ask'}
            </button>
          </form>
        </div>

        <div className="px-5 pb-5 space-y-4 overflow-y-auto">
          {history.length === 0 && !loading && (
            <p className="text-sm text-slate-500 text-center py-12">
              No questions asked yet this session.
            </p>
          )}
          {history.map((entry) => <AnswerCard key={entry.id} entry={entry} />)}
        </div>

      </div>
    </div>
  );
}
