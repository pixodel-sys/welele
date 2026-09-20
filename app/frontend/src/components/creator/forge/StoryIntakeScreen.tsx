import React, { useState, useEffect, useRef } from 'react';
import { storyForgeApi } from '../../../services/storyForgeApi';
import { StorySummary } from '../../../types/storyForge';
import {
  Sparkles,
  Flame,
  PlusCircle,
  FolderOpen,
  ArrowRight,
  BookOpen,
  Clapperboard,
  Layers,
  Globe,
  RefreshCw,
  AlertCircle,
  FileText,
  Upload
} from 'lucide-react';

interface StoryIntakeScreenProps {
  onStoryCreated: (
    storyId: string,
    initialPremise?: string,
    creativeObjective?: string,
    productionObjective?: string,
    documentContext?: string
  ) => void;
  onResumeStory: (storyId: string) => void;
}

export const StoryIntakeScreen: React.FC<StoryIntakeScreenProps> = ({
  onStoryCreated,
  onResumeStory,
}) => {
  const [activeTab, setActiveTab] = useState<'new' | 'resume'>('new');
  const [intakeMode, setIntakeMode] = useState<'premise' | 'document'>('premise');
  
  // New Story Form States
  const [title, setTitle] = useState('');
  const [premise, setPremise] = useState('');
  const [documentContext, setDocumentContext] = useState('');
  const [creativeObjective, setCreativeObjective] = useState('');
  const [productionObjective, setProductionObjective] = useState('');
  const [primaryLanguage, setPrimaryLanguage] = useState('isiZulu');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [documentValidationError, setDocumentValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Resume Stories State
  const [existingStories, setExistingStories] = useState<StorySummary[]>([]);
  const [isLoadingStories, setIsLoadingStories] = useState(false);

  useEffect(() => {
    if (activeTab === 'resume') {
      loadStories();
    }
  }, [activeTab]);

  const loadStories = async () => {
    setIsLoadingStories(true);
    try {
      const list = await storyForgeApi.listStories();
      setExistingStories(list);
    } catch (e: any) {
      console.warn('Could not load existing stories:', e);
    } finally {
      setIsLoadingStories(false);
    }
  };

  const handleDocumentTextChange = (text: string) => {
    const trimmed = text.trim();
    if (
      trimmed.startsWith('PK\x03\x04') ||
      trimmed.startsWith('PK\x05\x06') ||
      trimmed.startsWith('PK\x07\x08') ||
      trimmed.startsWith('PK\\x03\\x04') ||
      trimmed.startsWith('PK\\u0003\\u0004') ||
      trimmed.startsWith('PK\u0003\u0004') ||
      (trimmed.startsWith('PK') && trimmed.includes('[Content_Types].xml'))
    ) {
      setDocumentValidationError(
        'Unsupported binary DOCX/ZIP signature detected in text. Story Forge accepts clean plain text (.txt) and Markdown (.md) notes only.'
      );
    } else if (trimmed.startsWith('%PDF') || trimmed.startsWith('\\%PDF')) {
      setDocumentValidationError(
        'Unsupported binary PDF signature detected in text. Story Forge accepts clean plain text (.txt) and Markdown (.md) notes only.'
      );
    } else if (trimmed.startsWith('{\\rtf') || trimmed.startsWith('{\\\\rtf')) {
      setDocumentValidationError(
        'Unsupported RTF format detected in text. Story Forge accepts clean plain text (.txt) and Markdown (.md) notes only.'
      );
    } else if (text.includes('\x00') || text.includes('\\x00') || text.includes('\\u0000')) {
      setDocumentValidationError(
        'Corrupted text: null bytes detected. Document context must be clean UTF-8 plain text.'
      );
    } else {
      setDocumentValidationError(null);
    }
    setDocumentContext(text.slice(0, 15000));
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 1. Validate file extension before reading contents
    const fileName = file.name.toLowerCase();
    const extMatch = fileName.match(/\.([0-9a-z]+)$/i);
    const ext = extMatch ? extMatch[1] : '';

    if (ext !== 'txt' && ext !== 'md') {
      setDocumentValidationError(
        `Unsupported file format (.${ext || 'unknown'}). Story Forge currently supports plain text notes (.txt) and Markdown (.md) only. Binary documents (.docx, .pdf, .rtf) must be exported to plain text or Markdown before ingestion.`
      );
      // Never place rejected/garbled content into story context field
      setDocumentContext('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    // 2. Validate MIME / byte signature before decoding as text
    // Read initial 16-byte slice to check magic signatures
    const slice = file.slice(0, 16);
    const headerReader = new FileReader();

    headerReader.onload = () => {
      const buffer = headerReader.result as ArrayBuffer;
      const bytes = new Uint8Array(buffer);

      // Magic Byte Inspection:
      // ZIP / DOCX / OpenXML: PK\x03\x04 (0x50, 0x4B, 0x03, 0x04)
      const isZipDocx =
        bytes.length >= 4 &&
        bytes[0] === 0x50 &&
        bytes[1] === 0x4B &&
        (bytes[2] === 0x03 || bytes[2] === 0x05 || bytes[2] === 0x07);

      // PDF: %PDF (0x25, 0x50, 0x44, 0x46)
      const isPdf =
        bytes.length >= 4 &&
        bytes[0] === 0x25 &&
        bytes[1] === 0x50 &&
        bytes[2] === 0x44 &&
        bytes[3] === 0x46;

      // RTF: {\rtf (0x7B, 0x5C, 0x72, 0x74, 0x66)
      const isRtf =
        bytes.length >= 5 &&
        bytes[0] === 0x7B &&
        bytes[1] === 0x5C &&
        bytes[2] === 0x72 &&
        bytes[3] === 0x74 &&
        bytes[4] === 0x66;

      // Legacy MS Office OLE/DOC: 0xD0, 0xCF, 0x11, 0xE0
      const isLegacyDoc =
        bytes.length >= 4 &&
        bytes[0] === 0xD0 &&
        bytes[1] === 0xCF &&
        bytes[2] === 0x11 &&
        bytes[3] === 0xE0;

      // Null byte presence in header
      const hasNullByte = bytes.slice(0, 16).some((b) => b === 0);

      if (isZipDocx || isPdf || isRtf || isLegacyDoc || hasNullByte) {
        const detectedType = isZipDocx
          ? 'Word DOCX / ZIP container'
          : isPdf
          ? 'PDF document'
          : isRtf
          ? 'RTF document'
          : isLegacyDoc
          ? 'Legacy Word DOC'
          : 'Binary format';

        setDocumentValidationError(
          `Unsupported binary signature detected (${detectedType}). Story Forge accepts plain text notes (.txt) and Markdown (.md) only. Binary documents must never be decoded as plain text.`
        );
        // Never decode an unsupported binary document or place rejected/garbled content into story context field
        setDocumentContext('');
        if (fileInputRef.current) fileInputRef.current.value = '';
        return;
      }

      // 3. Only decode clean plain text after signature passes
      const contentReader = new FileReader();
      contentReader.onload = () => {
        const text = contentReader.result as string;
        if (text.includes('\x00')) {
          setDocumentValidationError(
            'Corrupted text document: null bytes detected. Only clean UTF-8 plain text (.txt) or Markdown (.md) is supported.'
          );
          setDocumentContext('');
          if (fileInputRef.current) fileInputRef.current.value = '';
          return;
        }

        setDocumentValidationError(null);
        setDocumentContext(text.slice(0, 15000));
        if (!title.trim()) {
          const derivedTitle = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
          setTitle(derivedTitle.charAt(0).toUpperCase() + derivedTitle.slice(1));
        }
      };
      contentReader.readAsText(file);
    };

    headerReader.readAsArrayBuffer(slice);
  };

  const handleCreateStory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setErrorMessage('Please provide a Story Title.');
      return;
    }

    if (intakeMode === 'premise' && !premise.trim()) {
      setErrorMessage('Please provide a starting Premise or switch to Document Submission Mode.');
      return;
    }

    if (intakeMode === 'document' && !documentContext.trim()) {
      setErrorMessage('Please paste or upload your story notes/treatment for Document Submission Mode.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    const effectivePremise = premise.trim() || (documentContext.trim().slice(0, 280) + '...');

    try {
      const created = await storyForgeApi.createStory({
        title: title.trim(),
        owner_id: 'creator_current',
        logline: effectivePremise,
        primary_language: primaryLanguage,
      });

      onStoryCreated(
        created.story_id,
        effectivePremise,
        creativeObjective.trim() || undefined,
        productionObjective.trim() || undefined,
        intakeMode === 'document' ? documentContext.trim() : undefined
      );
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to create story on Forge backend';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 space-y-6">
      {/* Top Banner */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FF6500]/10 border border-[#FF6500]/30 text-[#FF6500] text-xs font-mono font-bold uppercase tracking-wider">
          <Flame className="w-3.5 h-3.5" />
          <span>Story Forge™ Internal Narrative Reasoning</span>
          <span className="text-[11px] font-mono text-white/50 border-l border-white/20 pl-2">Forge Configuration: CFG-001</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-white font-sans tracking-tight">
          Creator Story Cockpit
        </h1>
        <p className="text-sm text-white/60 max-w-lg mx-auto">
          Begin with a raw premise or seed. The Forge kernel will discover characters, world rules, and episodic spines under your creative authority.
        </p>
      </div>

      {/* Mode Switcher */}
      <div className="flex items-center justify-center">
        <div className="p-1 rounded-xl bg-black/40 border border-white/10 flex items-center gap-1">
          <button
            onClick={() => setActiveTab('new')}
            className={`px-5 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'new'
                ? 'bg-[#FF6500] text-black shadow-lg shadow-[#FF6500]/25'
                : 'text-white/60 hover:text-white'
            }`}
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Start a New Story</span>
          </button>
          <button
            onClick={() => setActiveTab('resume')}
            className={`px-5 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'resume'
                ? 'bg-[#FF6500] text-black shadow-lg shadow-[#FF6500]/25'
                : 'text-white/60 hover:text-white'
            }`}
          >
            <FolderOpen className="w-3.5 h-3.5" />
            <span>Resume Existing Story</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-200 text-xs flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <p>{errorMessage}</p>
        </div>
      )}

      {/* TAB 1: NEW STORY (Blank Canvas) */}
      {activeTab === 'new' && (
        <form
          onSubmit={handleCreateStory}
          className="bg-[#12131C] border border-white/10 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-5"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-white/80 mb-1.5">
                Story Title <span className="text-[#FF6500]">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                spellCheck={true}
                placeholder="e.g. The Wrong Funeral"
                className="w-full px-4 py-3 rounded-xl bg-black/60 border border-white/15 focus:border-[#FF6500] focus:ring-1 focus:ring-[#FF6500] text-white text-sm placeholder-white/20 outline-none transition-all"
                required
              />
            </div>

            {/* Intake Sub-mode Selector */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-1.5 rounded-xl bg-black/40 border border-white/10">
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setIntakeMode('premise')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
                    intakeMode === 'premise'
                      ? 'bg-white/15 text-white shadow-sm border border-white/20'
                      : 'text-white/50 hover:text-white/80'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#FFA000]" />
                  <span>Quick Premise</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIntakeMode('document')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
                    intakeMode === 'document'
                      ? 'bg-purple-600/30 text-purple-200 shadow-sm border border-purple-500/40'
                      : 'text-white/50 hover:text-white/80'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 text-purple-400" />
                  <span>Document Submission Mode</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300">
                    Context Before Interrogation
                  </span>
                </button>
              </div>

              {intakeMode === 'document' && (
                <div className="flex items-center gap-2 pr-1">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".txt,.md,.text"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 hover:text-white text-xs border border-white/10 transition-colors font-mono"
                  >
                    <Upload className="w-3.5 h-3.5 text-[#FF6500]" />
                    <span>Upload Notes (.txt/.md)</span>
                  </button>
                </div>
              )}
            </div>

            {intakeMode === 'document' ? (
              <div className="space-y-3 p-5 rounded-2xl bg-purple-950/20 border border-purple-500/30">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-purple-300 uppercase tracking-wider">
                      <FileText className="w-4 h-4 text-purple-400" />
                      <span>Context Before Interrogation</span>
                    </div>
                    <p className="text-xs text-purple-200/80 leading-relaxed max-w-2xl">
                      Upload or paste existing story notes, treatment drafts, character rosters, or scene breakdowns.
                      Forge ingests this as deep narrative context up front—diving straight into dramatic tensions rather than interrogating you for baseline details.
                    </p>
                  </div>
                  <span className="text-[11px] font-mono text-white/40 shrink-0 self-end sm:self-auto">
                    {documentContext.length.toLocaleString()} / 15,000 chars
                  </span>
                </div>

                {documentValidationError && (
                  <div className="p-3.5 rounded-xl bg-rose-950/50 border border-rose-500/50 text-rose-200 text-xs flex items-start gap-2.5 shadow-lg">
                    <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                    <div className="space-y-0.5">
                      <span className="font-bold text-rose-100 block font-mono text-[11px] uppercase tracking-wider">
                        Document Input Guard
                      </span>
                      <span className="leading-relaxed">{documentValidationError}</span>
                    </div>
                  </div>
                )}

                <textarea
                  id="document-submission-context-textarea"
                  value={documentContext}
                  onChange={(e) => handleDocumentTextChange(e.target.value)}
                  rows={8}
                  spellCheck={true}
                  placeholder="Paste your story outline, treatment draft, scene breakdown, or character roster here...&#10;&#10;e.g.&#10;CHARACTERS:&#10;- Sabelo (32), disillusioned private investigator&#10;- Nomvula (28), heir to a contested taxi fleet&#10;&#10;PREMISE:&#10;In Durban, a series of staged break-ins leads back to a forgotten 2012 police report..."
                  className={`w-full px-4 py-3 rounded-xl bg-black/60 border text-white text-xs sm:text-sm placeholder-white/20 outline-none transition-all resize-none leading-relaxed font-mono ${
                    documentValidationError
                      ? 'border-rose-500/60 focus:border-rose-400 focus:ring-1 focus:ring-rose-400'
                      : 'border-purple-500/30 focus:border-purple-400 focus:ring-1 focus:ring-purple-400'
                  }`}
                  required
                />

                <div>
                  <label className="block text-[11px] font-mono font-bold uppercase tracking-wider text-white/60 mb-1">
                    Optional Story Logline / Focus Angle (Defaults to extracted notes if blank)
                  </label>
                  <input
                    type="text"
                    value={premise}
                    onChange={(e) => setPremise(e.target.value)}
                    spellCheck={true}
                    placeholder="e.g. A Durban detective is pulled into a family feud over a high-stakes taxi empire."
                    className="w-full px-3.5 py-2 rounded-xl bg-black/40 border border-white/10 text-white text-xs placeholder-white/20 outline-none focus:border-[#FF6500]"
                  />
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-mono font-bold uppercase tracking-wider text-white/80 mb-1.5">
                  Raw Story Material / Starting Premise <span className="text-[#FF6500]">*</span>
                </label>
                <textarea
                  value={premise}
                  onChange={(e) => setPremise(e.target.value)}
                  rows={4}
                  spellCheck={true}
                  placeholder="e.g. A man arrives at a funeral expecting to mourn his uncle. He quickly realises he is at the wrong funeral. Before he can leave, the family mistakes him for someone they have been waiting for."
                  className="w-full px-4 py-3 rounded-xl bg-black/60 border border-white/15 focus:border-[#FF6500] focus:ring-1 focus:ring-[#FF6500] text-white text-sm placeholder-white/20 outline-none transition-all resize-none leading-relaxed"
                  required
                />
                <p className="text-[11px] text-white/40 mt-1 font-mono">
                  The submission can be deliberately sparse. The Forge will formulate questions to resolve missing invariants.
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono font-bold uppercase tracking-wider text-white/70 mb-1.5">
                  Creative Objective (Optional)
                </label>
                <input
                  type="text"
                  value={creativeObjective}
                  onChange={(e) => setCreativeObjective(e.target.value)}
                  spellCheck={true}
                  placeholder="e.g. South African supernatural comedy / vertical microdrama"
                  className="w-full px-4 py-2.5 rounded-xl bg-black/60 border border-white/15 focus:border-[#FF6500] text-white text-xs placeholder-white/20 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold uppercase tracking-wider text-white/70 mb-1.5">
                  Production Objective (Optional)
                </label>
                <input
                  type="text"
                  value={productionObjective}
                  onChange={(e) => setProductionObjective(e.target.value)}
                  spellCheck={true}
                  placeholder="e.g. Low budget, primarily one funeral venue, episodic cliffhangers"
                  className="w-full px-4 py-2.5 rounded-xl bg-black/60 border border-white/15 focus:border-[#FF6500] text-white text-xs placeholder-white/20 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono font-bold uppercase tracking-wider text-white/70 mb-1.5">
                Primary Language
              </label>
              <select
                value={primaryLanguage}
                onChange={(e) => setPrimaryLanguage(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-black/60 border border-white/15 text-white text-xs outline-none"
              >
                <option value="isiZulu">isiZulu</option>
                <option value="English">English</option>
                <option value="isiXhosa">isiXhosa</option>
                <option value="Sesotho">Sesotho</option>
                <option value="Setswana">Setswana</option>
              </select>
            </div>
          </div>

          <div className="pt-4 border-t border-white/5 flex items-center justify-end">
            <button
              type="submit"
              disabled={
                isSubmitting ||
                !title.trim() ||
                (intakeMode === 'document'
                  ? !documentContext.trim() || !!documentValidationError
                  : !premise.trim())
              }
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#FF6500] to-[#FF8500] hover:from-[#FF7500] hover:to-[#FF9500] disabled:opacity-35 disabled:cursor-not-allowed text-black font-black text-xs uppercase tracking-wider transition-all flex items-center gap-2 shadow-xl shadow-[#FF6500]/20 active:scale-98"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Initializing Forge Session...</span>
                </>
              ) : (
                <>
                  <span>Enter Forge Session</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      )}

      {/* TAB 2: RESUME STORY */}
      {activeTab === 'resume' && (
        <div className="bg-[#12131C] border border-white/10 rounded-2xl p-6 shadow-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-white/80 font-mono">
              Saved Forge Stories ({existingStories.length})
            </h3>
            <button
              onClick={loadStories}
              disabled={isLoadingStories}
              className="text-xs text-white/50 hover:text-white flex items-center gap-1"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingStories ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          {isLoadingStories ? (
            <div className="py-12 text-center text-xs text-white/40 font-mono">
              Loading stories from Forge engine...
            </div>
          ) : existingStories.length === 0 ? (
            <div className="py-12 text-center text-xs text-white/40 font-mono space-y-2">
              <p>No existing stories found on this backend.</p>
              <button
                onClick={() => setActiveTab('new')}
                className="text-[#FF6500] hover:underline font-bold"
              >
                Create your first story →
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {existingStories.map((s) => (
                <div
                  key={s.id}
                  onClick={() => onResumeStory(s.id)}
                  className="p-4 rounded-xl bg-black/40 border border-white/10 hover:border-[#FF6500]/60 transition-all cursor-pointer group flex flex-col justify-between"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="px-2 py-0.5 rounded bg-white/10 text-white/80 font-bold">
                        v{s.current_state_version}
                      </span>
                      <span className="text-emerald-400 font-semibold">{s.status}</span>
                    </div>
                    <h4 className="text-base font-black text-white group-hover:text-[#FF6500] truncate">
                      {s.title}
                    </h4>
                    {s.logline && (
                      <p className="text-xs text-white/60 line-clamp-2 leading-relaxed">
                        {s.logline}
                      </p>
                    )}
                  </div>
                  <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-xs text-[#FF6500] font-bold">
                    <span>Resume Cockpit</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
