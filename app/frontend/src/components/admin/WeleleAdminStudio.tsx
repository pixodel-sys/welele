import React, { useState, useEffect, useRef } from 'react';
import { experienceApi } from '../../services/api';
import { ExperienceManifest, ExperienceSection, SlotItem, SectionType } from '../../types/experience';
import { Story } from '../../types';
import { ExperiencePageRenderer } from '../experience/ExperiencePageRenderer';
import { ProvenanceBadge } from '../common/patterns/ProvenanceBadge';
import {
  Layers,
  Smartphone,
  Tablet,
  Monitor,
  Eye,
  EyeOff,
  MoveUp,
  MoveDown,
  Plus,
  Trash2,
  Copy,
  Save,
  Send,
  RotateCcw,
  Sparkles,
  Calendar,
  CheckCircle2,
  AlertCircle,
  GripVertical,
  SlidersHorizontal,
  Maximize2,
  ZoomIn,
  ZoomOut,
  Info,
  Radio,
  X
} from 'lucide-react';

interface WeleleAdminStudioProps {
  stories: Story[];
}

export const WeleleAdminStudio: React.FC<WeleleAdminStudioProps> = ({ stories }) => {
  const [selectedPage, setSelectedPage] = useState<string>('home');
  const [manifest, setManifest] = useState<ExperienceManifest | null>(null);
  const [liveManifest, setLiveManifest] = useState<ExperienceManifest | null>(null);
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
  const [viewportPreset, setViewportPreset] = useState<number>(1024); // Default to desktop 1024px or 390px
  const [isFitMode, setIsFitMode] = useState<boolean>(true); // Fit by default to let experience breathe
  const [zoomScale, setZoomScale] = useState<number>(100);
  const [simulatedTime, setSimulatedTime] = useState<string>('');
  const [saving, setSaving] = useState<boolean>(false);
  const [publishing, setPublishing] = useState<boolean>(false);
  const [isLiveModalOpen, setIsLiveModalOpen] = useState<boolean>(false);
  const [notification, setNotification] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [lastSaved, setLastSaved] = useState<string>('Just now');

  const controlPanelRef = useRef<HTMLDivElement>(null);
  const inspectorSectionRef = useRef<HTMLDivElement>(null);
  const previewScrollContainerRef = useRef<HTMLDivElement>(null);

  // Load draft experience
  const loadDraft = async (pageId: string) => {
    try {
      const data = await experienceApi.getPreviewExperience(pageId, 'draft', simulatedTime || undefined);
      setManifest(data);
      if (data.sections.length > 0 && !selectedSectionId) {
        setSelectedSectionId(data.sections[0].section_id);
      }
      if (data.updated_at) {
        const d = new Date(data.updated_at);
        setLastSaved(d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      }
    } catch (err) {
      console.error('Failed to load draft:', err);
      showNotification('Failed to load page layout', 'error');
    }
  };

  // Load live published experience for comparison
  const loadLive = async (pageId: string) => {
    try {
      const liveData = await experienceApi.getPageExperience(pageId);
      setLiveManifest(liveData);
    } catch (err) {
      console.warn('Could not load live manifest:', err);
    }
  };

  useEffect(() => {
    loadDraft(selectedPage);
    loadLive(selectedPage);
  }, [selectedPage, simulatedTime]);

  const showNotification = (text: string, type: 'success' | 'error') => {
    setNotification({ text, type });
    setTimeout(() => setNotification(null), 4000);
  };

  if (!manifest) {
    return <div className="p-12 text-center text-welele-muted">Loading Experience Studio...</div>;
  }

  const selectedSection = manifest.sections.find((s) => s.section_id === selectedSectionId);

  // Synchronised selection & scroll handling
  const handleSelectSection = (sectionId: string, origin: 'tree' | 'preview' | 'inspector' = 'tree') => {
    setSelectedSectionId(sectionId);

    if (origin === 'tree' || origin === 'inspector') {
      setTimeout(() => {
        const previewEl = document.getElementById(`preview-sec-${sectionId}`);
        if (previewEl) {
          previewEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 50);
    }

    if (origin === 'preview') {
      setTimeout(() => {
        const treeEl = document.getElementById(`tree-sec-${sectionId}`);
        if (treeEl) {
          treeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        if (inspectorSectionRef.current) {
          inspectorSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 50);
    }
  };

  // Section Reordering
  const moveSection = (index: number, direction: 'up' | 'down') => {
    const targetIdx = direction === 'up' ? index - 1 : index + 1;
    if (targetIdx < 0 || targetIdx >= manifest.sections.length) return;

    const updatedSections = [...manifest.sections];
    const temp = updatedSections[index];
    updatedSections[index] = updatedSections[targetIdx];
    updatedSections[targetIdx] = temp;

    updatedSections.forEach((s, idx) => {
      s.order = idx;
    });

    setManifest({ ...manifest, sections: updatedSections });
  };

  // Toggle Visibility
  const toggleVisibility = (sectionId: string) => {
    const updatedSections = manifest.sections.map((s) =>
      s.section_id === sectionId ? { ...s, is_visible: !s.is_visible } : s
    );
    setManifest({ ...manifest, sections: updatedSections });
  };

  // Duplicate Section
  const duplicateSection = (section: ExperienceSection) => {
    const cloned: ExperienceSection = {
      ...JSON.parse(JSON.stringify(section)),
      section_id: `sec_${section.type.toLowerCase()}_${Date.now().toString().slice(-4)}`,
      title: section.title ? `${section.title} (Copy)` : 'Cloned Section',
      order: manifest.sections.length,
    };
    setManifest({
      ...manifest,
      sections: [...manifest.sections, cloned],
    });
    setSelectedSectionId(cloned.section_id);
    showNotification('Section duplicated', 'success');
  };

  // Delete Section
  const deleteSection = (sectionId: string) => {
    const updated = manifest.sections.filter((s) => s.section_id !== sectionId);
    setManifest({ ...manifest, sections: updated });
    if (selectedSectionId === sectionId) {
      if (updated.length > 0) {
        setSelectedSectionId(updated[0].section_id);
      } else {
        setSelectedSectionId(null);
      }
    }
  };

  // Add Section
  const addSection = (type: SectionType) => {
    const newSec: ExperienceSection = {
      section_id: `sec_${type.toLowerCase()}_${Date.now().toString().slice(-4)}`,
      type,
      title: type === 'HERO_CAROUSEL' ? null : 'New Curated Section',
      subtitle: 'Editorial collection subtitle',
      is_visible: true,
      order: manifest.sections.length,
      config: {
        card_size: 'medium',
        aspect_ratio: '9:16',
        show_rank_numbers: false,
      },
      source: {
        mode: 'manual',
        max_items: 8,
        pinned_content_ids: stories.slice(0, 4).map((s) => s.id),
      },
      items: [],
    };

    setManifest({
      ...manifest,
      sections: [...manifest.sections, newSec],
    });
    handleSelectSection(newSec.section_id, 'tree');
  };

  // Save Draft
  const handleSaveDraft = async () => {
    setSaving(true);
    try {
      await experienceApi.saveDraft(selectedPage, {
        meta: manifest.meta,
        sections: manifest.sections,
      });
      setLastSaved('Just now');
      showNotification('Draft layout saved successfully', 'success');
    } catch (err) {
      showNotification('Failed to save draft', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Publish to LIVE
  const handlePublish = async () => {
    setPublishing(true);
    try {
      await experienceApi.saveDraft(selectedPage, {
        meta: manifest.meta,
        sections: manifest.sections,
      });
      const res = await experienceApi.publish(selectedPage);
      showNotification(`Published Live! Version: ${res.version}`, 'success');
      loadDraft(selectedPage);
      loadLive(selectedPage);
    } catch (err) {
      showNotification('Failed to publish experience', 'error');
    } finally {
      setPublishing(false);
    }
  };

  // Reset to Defaults
  const handleReset = async () => {
    if (window.confirm('Reset this page to canonical default layout?')) {
      await experienceApi.resetDefault(selectedPage);
      loadDraft(selectedPage);
      loadLive(selectedPage);
      showNotification('Reset to canonical preset', 'success');
    }
  };

  const viewportPresets = [
    { label: '360', width: 360, type: 'Mobile (360px)', icon: Smartphone },
    { label: '390', width: 390, type: 'Mobile Pro (390px)', icon: Smartphone },
    { label: '768', width: 768, type: 'Tablet (768px)', icon: Tablet },
    { label: '1024', width: 1024, type: 'Desktop (1024px)', icon: Monitor },
    { label: '1440', width: 1440, type: 'Wide Desktop (1440px)', icon: Monitor },
  ];

  // Calculate viewport style to let rendered experience breathe naturally
  const getViewportStyle = () => {
    if (isFitMode) {
      if (viewportPreset <= 440) {
        return {
          width: '100%',
          maxWidth: '430px',
          transform: zoomScale !== 100 ? `scale(${zoomScale / 100})` : 'none',
          transformOrigin: 'top center',
        };
      }
      if (viewportPreset === 768) {
        return {
          width: '100%',
          maxWidth: '768px',
          transform: zoomScale !== 100 ? `scale(${zoomScale / 100})` : 'none',
          transformOrigin: 'top center',
        };
      }
      return {
        width: '100%',
        maxWidth: '100%',
        transform: zoomScale !== 100 ? `scale(${zoomScale / 100})` : 'none',
        transformOrigin: 'top center',
      };
    }

    return {
      width: `${viewportPreset}px`,
      maxWidth: '100%',
      transform: zoomScale !== 100 ? `scale(${zoomScale / 100})` : 'none',
      transformOrigin: 'top center',
    };
  };

  return (
    <div className="w-full space-y-4 text-white font-sans">
      {/* ========================================================================= */}
      {/* TOP COMMAND TOOLBAR — Width 100% Flush Aligned with Admin Console          */}
      {/* ========================================================================= */}
      <div className="w-full p-4 rounded-[7px] bg-welele-surface-2 border border-white/10 shadow-2xl flex flex-col xl:flex-row items-start xl:items-center justify-between gap-4">
        {/* Left: Brand, Draft Status & Page Selector */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="w-10 h-10 rounded-[7px] bg-gradient-to-tr from-welele-orange to-amber-400 flex items-center justify-center text-black shadow-lg shrink-0">
            <Layers className="w-5 h-5 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-sm sm:text-base font-black text-[#FFF8F0] tracking-tight uppercase">
                Welele Experience Studio
              </h2>
              <span className="px-2 py-0.5 rounded-[7px] text-[9px] font-bold bg-welele-orange/20 text-welele-orange border border-welele-orange/30 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-welele-orange animate-pulse" />
                DRAFT
              </span>
              <span className="text-[10px] text-welele-muted">
                Last saved {lastSaved}
              </span>
            </div>
            <p className="text-[11px] text-welele-muted">
              Dynamic surface engine & responsive experience workspace
            </p>
          </div>

          <div className="ml-0 sm:ml-2">
            <select
              value={selectedPage}
              onChange={(e) => setSelectedPage(e.target.value)}
              className="px-3 py-1.5 rounded-[7px] bg-welele-surface border border-white/10 text-xs font-bold text-white focus:outline-none cursor-pointer"
            >
              <option value="home">Home / Showcase Surface</option>
              <option value="discover">Discover / Catalog Surface</option>
            </select>
          </div>
        </div>

        {/* Center: Viewport Presets, Fit Mode & Zoom Controls */}
        <div className="flex items-center gap-2 flex-wrap bg-[#101114] p-1.5 rounded-[7px] border border-white/5">
          <div className="flex items-center gap-1">
            {viewportPresets.map((preset) => {
              const isSelected = viewportPreset === preset.width && !isFitMode;
              return (
                <button
                  key={preset.label}
                  onClick={() => {
                    setViewportPreset(preset.width);
                    setIsFitMode(false);
                  }}
                  className={`px-2.5 py-1.5 rounded-[7px] text-xs font-bold transition-all cursor-pointer flex items-center gap-1 ${
                    isSelected
                      ? 'bg-welele-orange text-black shadow-md'
                      : 'text-white/70 hover:text-white hover:bg-white/5'
                  }`}
                  title={preset.type}
                >
                  <preset.icon className="w-3 h-3" />
                  <span>{preset.label}</span>
                </button>
              );
            })}

            {/* Smart Fit Option */}
            <button
              onClick={() => setIsFitMode(!isFitMode)}
              className={`px-3 py-1.5 rounded-[7px] text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                isFitMode
                  ? 'bg-welele-orange text-black shadow-md'
                  : 'text-white/70 hover:text-white hover:bg-white/5'
              }`}
              title="Fit viewport cleanly to available preview canvas"
            >
              <Maximize2 className="w-3 h-3" />
              <span>Fit</span>
            </button>
          </div>

          {/* Zoom − / % / + */}
          <div className="flex items-center gap-1 border-l border-white/10 pl-2">
            <button
              onClick={() => setZoomScale((prev) => Math.max(75, prev - 10))}
              className="p-1.5 rounded-[7px] text-white/70 hover:text-white hover:bg-white/10 cursor-pointer"
              title="Zoom out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-[10px] font-mono font-bold text-welele-orange min-w-[36px] text-center">
              {zoomScale}%
            </span>
            <button
              onClick={() => setZoomScale((prev) => Math.min(130, prev + 10))}
              className="p-1.5 rounded-[7px] text-white/70 hover:text-white hover:bg-white/10 cursor-pointer"
              title="Zoom in"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right: Actions (View Live, Save Draft, Publish, Reset) */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setIsLiveModalOpen(true)}
            className="px-3.5 py-2 rounded-[7px] bg-white/5 hover:bg-white/15 border border-white/10 text-xs font-semibold text-white/90 flex items-center gap-1.5 transition-all cursor-pointer"
            title="Compare current draft against live published manifest"
          >
            <Radio className="w-3.5 h-3.5 text-emerald-400" />
            <span>View Live</span>
          </button>

          <button
            onClick={handleSaveDraft}
            disabled={saving}
            className="px-4 py-2 rounded-[7px] bg-white/10 hover:bg-white/20 border border-white/10 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <Save className="w-3.5 h-3.5" />
            {saving ? 'Saving...' : 'Save Draft'}
          </button>

          <button
            onClick={handlePublish}
            disabled={publishing}
            className="px-4 py-2 rounded-[7px] bg-gradient-to-r from-welele-orange to-amber-500 hover:from-orange-600 text-black text-xs font-extrabold flex items-center gap-1.5 shadow-lg shadow-welele-orange/20 transition-all cursor-pointer"
          >
            <Send className="w-3.5 h-3.5 fill-black" />
            {publishing ? 'Publishing...' : 'Publish to LIVE'}
          </button>

          <button
            onClick={handleReset}
            className="p-2 rounded-[7px] bg-white/5 hover:bg-white/10 border border-white/5 text-white/60 hover:text-white transition-all cursor-pointer"
            title="Reset to canonical default preset"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {notification && (
        <div
          className={`p-3 rounded-[7px] text-xs font-bold flex items-center gap-2 shadow-xl animate-fade-in ${
            notification.type === 'success'
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
              : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
          }`}
        >
          {notification.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4" />
          ) : (
            <AlertCircle className="w-4 h-4" />
          )}
          <span>{notification.text}</span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2-COLUMN WORKSPACE: 380px Left Controls | ~850px+ Expanded Preview Canvas */}
      {/* ========================================================================= */}
      <div className="flex flex-col lg:flex-row gap-5 items-start w-full">
        
        {/* ======================================================================= */}
        {/* LEFT COLUMN: Experience Tree + Section Inspector (380px fixed width)    */}
        {/* ======================================================================= */}
        <div
          ref={controlPanelRef}
          className="w-full lg:w-[380px] shrink-0 space-y-4 max-h-[calc(100vh-140px)] min-h-[720px] overflow-y-auto pr-1 scrollbar-thin"
        >
          {/* SECTION 1: EXPERIENCE HIERARCHY TREE */}
          <div className="rounded-[7px] bg-welele-surface-2 border border-white/10 shadow-2xl p-4 sm:p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h3 className="text-sm font-black uppercase tracking-wider text-white">
                  Experience Tree
                </h3>
                <span className="text-[11px] text-welele-muted">
                  {manifest.sections.length} Sections • Click to highlight & sync
                </span>
              </div>

              {/* Add Section Dropdown */}
              <div className="relative group">
                <button className="px-3 py-1.5 rounded-[7px] bg-welele-orange text-black font-extrabold text-xs flex items-center gap-1 shadow-lg cursor-pointer hover:bg-orange-500 transition-colors">
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Section</span>
                </button>
                <div className="absolute right-0 mt-1 w-56 bg-[#16171B] border border-white/10 rounded-[7px] shadow-2xl p-2 hidden group-hover:block z-30 space-y-1">
                  <button
                    onClick={() => addSection('HERO_CAROUSEL')}
                    className="w-full text-left px-3 py-2 rounded-[7px] text-xs font-semibold hover:bg-white/10 text-white cursor-pointer"
                  >
                    + Hero Carousel
                  </button>
                  <button
                    onClick={() => addSection('HORIZONTAL_ROW')}
                    className="w-full text-left px-3 py-2 rounded-[7px] text-xs font-semibold hover:bg-white/10 text-white cursor-pointer"
                  >
                    + Horizontal Content Row
                  </button>
                  <button
                    onClick={() => addSection('EDITORIAL_BANNER')}
                    className="w-full text-left px-3 py-2 rounded-[7px] text-xs font-semibold hover:bg-white/10 text-white cursor-pointer"
                  >
                    + Editorial Banner
                  </button>
                  <button
                    onClick={() => addSection('EDITORIAL_SPOTLIGHT')}
                    className="w-full text-left px-3 py-2 rounded-[7px] text-xs font-semibold hover:bg-white/10 text-white cursor-pointer"
                  >
                    + Spotlight Showcase Card
                  </button>
                  <button
                    onClick={() => addSection('POSTER_GRID')}
                    className="w-full text-left px-3 py-2 rounded-[7px] text-xs font-semibold hover:bg-white/10 text-white cursor-pointer"
                  >
                    + Poster Grid
                  </button>
                  <button
                    onClick={() => addSection('COMING_SOON_RADAR')}
                    className="w-full text-left px-3 py-2 rounded-[7px] text-xs font-semibold hover:bg-white/10 text-white cursor-pointer"
                  >
                    + Coming Soon Radar
                  </button>
                </div>
              </div>
            </div>

            {/* Section Item Cards */}
            <div className="space-y-2">
              {manifest.sections.map((section, idx) => {
                const isSelected = section.section_id === selectedSectionId;
                const itemCount = section.items?.length || 0;
                const modeText =
                  section.source?.mode === 'algorithmic'
                    ? 'Algorithmic Ingestion'
                    : section.source?.mode === 'hybrid'
                    ? 'Hybrid (Curated + Auto)'
                    : `${itemCount} Curated Slots`;

                return (
                  <div
                    key={section.section_id}
                    id={`tree-sec-${section.section_id}`}
                    onClick={() => handleSelectSection(section.section_id, 'tree')}
                    className={`p-3.5 rounded-[7px] border transition-all cursor-pointer flex items-center justify-between gap-2.5 group ${
                      isSelected
                        ? 'bg-welele-orange/15 border-welele-orange text-white shadow-lg shadow-welele-orange/10 scale-[1.01]'
                        : 'bg-welele-surface border-white/5 text-white/90 hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0 flex-1">
                      <GripVertical className="w-4 h-4 text-white/30 group-hover:text-white/60 shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-[9px] font-mono font-bold text-welele-orange uppercase">
                            {section.type.replace('_', ' ')}
                          </span>
                          {!section.is_visible && (
                            <span className="text-[8px] font-bold px-1.5 py-0.2 rounded-[7px] bg-rose-500/20 text-rose-400 border border-rose-500/30">
                              Hidden
                            </span>
                          )}
                          <ProvenanceBadge
                            tier={section.source?.mode === 'algorithmic' ? 'SYSTEM_DERIVED' : 'ADMIN_CONTROLLED'}
                            label={section.source?.mode === 'algorithmic' ? 'SYSTEM / RULE_BASED' : 'ADMIN_CURATED'}
                            size="sm"
                          />
                        </div>
                        <p className="text-xs font-bold truncate mt-0.5">
                          {section.title ||
                            (section.type === 'HERO_CAROUSEL'
                              ? 'Hero Spotlight Carousel'
                              : section.type === 'EDITORIAL_BANNER'
                              ? 'Editorial Promo Banner'
                              : 'Untitled Section')}
                        </p>
                        <span className="text-[10px] text-welele-muted block mt-0.5">
                          {modeText}
                        </span>
                      </div>
                    </div>

                    {/* Quick Reorder & Control Actions */}
                    <div
                      className="flex items-center gap-1 shrink-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={() => moveSection(idx, 'up')}
                        disabled={idx === 0}
                        className="p-1 rounded-[7px] hover:bg-white/10 disabled:opacity-20 text-white/70 transition-colors cursor-pointer"
                        title="Move Up"
                      >
                        <MoveUp className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => moveSection(idx, 'down')}
                        disabled={idx === manifest.sections.length - 1}
                        className="p-1 rounded-[7px] hover:bg-white/10 disabled:opacity-20 text-white/70 transition-colors cursor-pointer"
                        title="Move Down"
                      >
                        <MoveDown className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => toggleVisibility(section.section_id)}
                        className="p-1 rounded-[7px] hover:bg-white/10 text-white/70 transition-colors cursor-pointer"
                        title="Toggle Visibility"
                      >
                        {section.is_visible ? (
                          <Eye className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <EyeOff className="w-3.5 h-3.5 text-rose-400" />
                        )}
                      </button>
                      <button
                        onClick={() => duplicateSection(section)}
                        className="p-1 rounded-[7px] hover:bg-white/10 text-white/70 transition-colors cursor-pointer"
                        title="Duplicate Section"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => deleteSection(section.section_id)}
                        className="p-1 rounded-[7px] hover:bg-rose-500/20 text-rose-400 transition-colors cursor-pointer"
                        title="Delete Section"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* SECTION 2: SECTION INSPECTOR (STACKED DIRECTLY BELOW TREE) */}
          <div
            ref={inspectorSectionRef}
            className="rounded-[7px] bg-welele-surface-2 border border-white/10 shadow-2xl p-4 sm:p-5 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-welele-orange" />
                <h3 className="text-sm font-black uppercase tracking-wider text-white">
                  Section Inspector
                </h3>
              </div>
              {selectedSection && (
                <span className="text-[10px] font-mono font-bold text-welele-orange px-2 py-0.5 rounded-[7px] bg-welele-orange/10 border border-welele-orange/20">
                  {selectedSection.type}
                </span>
              )}
            </div>

            {selectedSection ? (
              <div className="space-y-4">
                {/* Title & Subtitle Override */}
                {selectedSection.type !== 'HERO_CAROUSEL' && (
                  <div className="space-y-3">
                    <div>
                      <label className="text-[11px] font-bold text-welele-muted block mb-1">
                        Header Display Title
                      </label>
                      <input
                        type="text"
                        value={selectedSection.title || ''}
                        onChange={(e) => {
                          const updated = manifest.sections.map((s) =>
                            s.section_id === selectedSection.section_id
                              ? { ...s, title: e.target.value }
                              : s
                          );
                          setManifest({ ...manifest, sections: updated });
                        }}
                        className="w-full px-3 py-2 rounded-[7px] bg-welele-surface border border-white/10 text-xs text-white focus:border-welele-orange focus:outline-none"
                        placeholder="e.g. Trending Across Mzansi"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-bold text-welele-muted block mb-1">
                        Subtitle / Editorial Tagline
                      </label>
                      <input
                        type="text"
                        value={selectedSection.subtitle || ''}
                        onChange={(e) => {
                          const updated = manifest.sections.map((s) =>
                            s.section_id === selectedSection.section_id
                              ? { ...s, subtitle: e.target.value }
                              : s
                          );
                          setManifest({ ...manifest, sections: updated });
                        }}
                        className="w-full px-3 py-2 rounded-[7px] bg-welele-surface border border-white/10 text-xs text-white focus:border-welele-orange focus:outline-none"
                        placeholder="e.g. Top cliffhangers gripping South Africa this week"
                      />
                    </div>
                  </div>
                )}

                {/* Ingestion Mode */}
                <div className="space-y-2 pt-2 border-t border-white/10">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] font-bold text-welele-muted block">
                      Placement Origin & Ingestion Mode
                    </label>
                    <ProvenanceBadge
                      tier={selectedSection.source.mode === 'algorithmic' ? 'SYSTEM_DERIVED' : 'ADMIN_CONTROLLED'}
                      label={selectedSection.source.mode === 'algorithmic' ? 'SYSTEM / RULE_BASED' : 'ADMIN_CURATED'}
                      size="sm"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-1.5 bg-welele-surface p-1 rounded-[7px] border border-white/5 text-xs">
                    {(['manual', 'hybrid', 'algorithmic'] as const).map((mode) => (
                      <button
                        key={mode}
                        onClick={() => {
                          const updated = manifest.sections.map((s) =>
                            s.section_id === selectedSection.section_id
                              ? { ...s, source: { ...s.source, mode } }
                              : s
                          );
                          setManifest({ ...manifest, sections: updated });
                        }}
                        className={`py-1.5 rounded-[7px] font-bold capitalize transition-all cursor-pointer ${
                          selectedSection.source.mode === mode
                            ? 'bg-welele-orange text-black shadow-md'
                            : 'text-white/60 hover:text-white'
                        }`}
                      >
                        {mode}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Slot Manager */}
                <div className="space-y-3 pt-2 border-t border-white/10">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-white flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-welele-orange" />
                      Content Slots ({selectedSection.items?.length || 0})
                    </label>
                    <button
                      onClick={() => {
                        const newSlot: SlotItem = {
                          slot_id: `slot_${Date.now().toString().slice(-4)}`,
                          content_type: 'series',
                          content_id: stories[0]?.id || 'story_blood_ties',
                          badge: 'SPOTLIGHT ORIGINAL',
                          headline_override: '',
                          subheadline_override: '',
                          cta_text: 'Watch Now',
                          is_active: true,
                        };
                        const updated = manifest.sections.map((s) =>
                          s.section_id === selectedSection.section_id
                            ? { ...s, items: [...(s.items || []), newSlot] }
                            : s
                        );
                        setManifest({ ...manifest, sections: updated });
                      }}
                      className="px-2.5 py-1 rounded-[7px] bg-welele-orange/20 hover:bg-welele-orange/30 text-welele-orange border border-welele-orange/30 text-[10px] font-bold flex items-center gap-1 cursor-pointer transition-colors"
                    >
                      <Plus className="w-3 h-3" /> Add Slot
                    </button>
                  </div>

                  <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1 scrollbar-thin">
                    {(selectedSection.items || []).map((slot, sIdx) => (
                      <div
                        key={slot.slot_id || sIdx}
                        className="p-3.5 rounded-[7px] bg-welele-surface border border-white/10 space-y-2.5 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-welele-orange">Slot #{sIdx + 1}</span>
                          <button
                            onClick={() => {
                              const updatedItems = selectedSection.items.filter((_, idx) => idx !== sIdx);
                              const updated = manifest.sections.map((s) =>
                                s.section_id === selectedSection.section_id
                                  ? { ...s, items: updatedItems }
                                  : s
                              );
                              setManifest({ ...manifest, sections: updated });
                            }}
                            className="p-1 rounded-[7px] text-rose-400 hover:bg-rose-500/20 cursor-pointer transition-colors"
                            title="Remove slot"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>

                        {/* Series Content Picker */}
                        <div>
                          <label className="text-[10px] font-bold text-welele-muted block mb-0.5">
                            Target Series
                          </label>
                          <select
                            value={slot.content_id || ''}
                            onChange={(e) => {
                              const updatedItems = [...selectedSection.items];
                              updatedItems[sIdx] = { ...updatedItems[sIdx], content_id: e.target.value };
                              const updated = manifest.sections.map((s) =>
                                s.section_id === selectedSection.section_id
                                  ? { ...s, items: updatedItems }
                                  : s
                              );
                              setManifest({ ...manifest, sections: updated });
                            }}
                            className="w-full px-2.5 py-1.5 rounded-[7px] bg-black/40 border border-white/10 text-white font-semibold focus:outline-none"
                          >
                            {stories.map((st) => (
                              <option key={st.id} value={st.id}>
                                {st.title} ({st.genre?.split('•')[0]})
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Badge Override */}
                        <div>
                          <label className="text-[10px] font-bold text-welele-muted block mb-0.5">
                            Badge Override
                          </label>
                          <input
                            type="text"
                            placeholder="e.g. SPOTLIGHT ORIGINAL, TOP 10"
                            value={slot.badge || ''}
                            onChange={(e) => {
                              const updatedItems = [...selectedSection.items];
                              updatedItems[sIdx] = { ...updatedItems[sIdx], badge: e.target.value };
                              const updated = manifest.sections.map((s) =>
                                s.section_id === selectedSection.section_id
                                  ? { ...s, items: updatedItems }
                                  : s
                              );
                              setManifest({ ...manifest, sections: updated });
                            }}
                            className="w-full px-2.5 py-1.5 rounded-[7px] bg-black/40 border border-white/10 text-white focus:outline-none"
                          />
                        </div>

                        {/* Headline Override */}
                        <div>
                          <label className="text-[10px] font-bold text-welele-muted block mb-0.5">
                            Custom Title Override
                          </label>
                          <input
                            type="text"
                            placeholder="Leave blank to use default title"
                            value={slot.headline_override || ''}
                            onChange={(e) => {
                              const updatedItems = [...selectedSection.items];
                              updatedItems[sIdx] = { ...updatedItems[sIdx], headline_override: e.target.value };
                              const updated = manifest.sections.map((s) =>
                                s.section_id === selectedSection.section_id
                                  ? { ...s, items: updatedItems }
                                  : s
                              );
                              setManifest({ ...manifest, sections: updated });
                            }}
                            className="w-full px-2.5 py-1.5 rounded-[7px] bg-black/40 border border-white/10 text-white focus:outline-none"
                          />
                        </div>

                        {/* Button CTA Text */}
                        <div>
                          <label className="text-[10px] font-bold text-welele-muted block mb-0.5">
                            Button CTA Text
                          </label>
                          <input
                            type="text"
                            placeholder="e.g. Watch Now"
                            value={slot.cta_text || ''}
                            onChange={(e) => {
                              const updatedItems = [...selectedSection.items];
                              updatedItems[sIdx] = { ...updatedItems[sIdx], cta_text: e.target.value };
                              const updated = manifest.sections.map((s) =>
                                s.section_id === selectedSection.section_id
                                  ? { ...s, items: updatedItems }
                                  : s
                              );
                              setManifest({ ...manifest, sections: updated });
                            }}
                            className="w-full px-2.5 py-1.5 rounded-[7px] bg-black/40 border border-white/10 text-white focus:outline-none"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-welele-muted text-xs space-y-1">
                <Info className="w-6 h-6 mx-auto opacity-40 text-welele-orange" />
                <p>Select any section from the Experience Tree to configure its settings and slots.</p>
              </div>
            )}
          </div>
        </div>

        {/* ======================================================================= */}
        {/* RIGHT COLUMN: Expansive Experience Preview (~850px+ of available canvas)*/}
        {/* ======================================================================= */}
        <div className="flex-1 min-w-0 w-full rounded-[7px] bg-welele-surface-2 border border-white/10 shadow-2xl p-3 sm:p-4 flex flex-col max-h-[calc(100vh-140px)] min-h-[720px]">
          {/* Streamlined Viewport Workspace — Experience Visually Dominates */}
          <div className="flex-1 bg-[#060709] rounded-[7px] border border-white/5 overflow-y-auto flex justify-center items-start p-3 sm:p-6 scrollbar-thin">
            <div
              ref={previewScrollContainerRef}
              style={getViewportStyle()}
              className="bg-[#0B0C0E] rounded-[7px] border border-white/10 p-3 sm:p-5 shadow-2xl overflow-hidden shrink-0 transition-all duration-300"
            >
              <ExperiencePageRenderer
                pageId={selectedPage}
                manifestOverride={manifest}
                highlightedSectionId={selectedSectionId}
                onSectionClick={(secId) => handleSelectSection(secId, 'preview')}
                onOpenPlayer={(s) => alert(`[Simulator Play] ${s.title}`)}
                onOpenStoryDetail={(s) => alert(`[Simulator Detail] ${s.title}`)}
                onOpenPaymentModal={() => alert('[Simulator Payment Modal]')}
              />
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* "VIEW LIVE" PRODUCTION COMPARISON MODAL                                   */}
      {/* ========================================================================= */}
      {isLiveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fade-in">
          <div className="bg-welele-surface-2 border border-white/10 rounded-[7px] w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 sm:p-5 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-[7px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-bold">
                  <Radio className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-black text-white">
                    Live Production Surface — {selectedPage === 'home' ? 'Home Showcase' : 'Discover'}
                  </h3>
                  <p className="text-xs text-welele-muted">
                    Active contract live to all African mobile & desktop viewers (Version: {liveManifest?.version || 'LIVE'})
                  </p>
                </div>
              </div>

              <button
                onClick={() => setIsLiveModalOpen(false)}
                className="p-2 rounded-[7px] bg-white/5 hover:bg-white/10 text-white/70 hover:text-white cursor-pointer transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content / Live Manifest Viewport */}
            <div className="flex-1 p-4 sm:p-6 overflow-y-auto bg-[#060709] scrollbar-thin flex justify-center">
              <div className="w-full max-w-[540px] bg-[#0B0C0E] rounded-[7px] border border-white/10 p-4 shadow-2xl">
                {liveManifest ? (
                  <ExperiencePageRenderer
                    pageId={selectedPage}
                    manifestOverride={liveManifest}
                    onOpenPlayer={(s) => alert(`[Live Player] ${s.title}`)}
                    onOpenStoryDetail={(s) => alert(`[Live Detail] ${s.title}`)}
                    onOpenPaymentModal={() => alert('[Live Payment Modal]')}
                  />
                ) : (
                  <div className="p-12 text-center text-welele-muted text-xs">
                    Loading live production manifest...
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-white/10 bg-welele-surface flex items-center justify-between text-xs">
              <span className="text-welele-muted">
                {liveManifest?.sections?.length || 0} active sections live
              </span>
              <button
                onClick={() => setIsLiveModalOpen(false)}
                className="px-4 py-2 rounded-[7px] bg-white/10 hover:bg-white/20 text-white font-bold cursor-pointer"
              >
                Close Comparison
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
