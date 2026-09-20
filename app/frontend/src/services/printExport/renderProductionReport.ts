/**
 * Welele Media™ — Print Export Engine v1.0
 * Renders A4 Portrait Printable Production Report over canonical Welele state.
 */

import { PrintableProductionReportData } from "./printExport.types";

export function renderAndOpenProductionReport(data: PrintableProductionReportData) {
  const printWin = window.open("", "_blank");
  if (!printWin) {
    alert("Please allow popups to open the printable Welele Production Report.");
    return;
  }

  const studioName = data.brand.studioName || "WELELE MEDIA™";
  const studioTagline = data.brand.studioTagline || "The Story OS for African Cinema";
  const accent = data.brand.accentColor || "#FF6500";
  const meta = data.metadata;

  const charactersHtml = data.characterBible.map((c) => `
    <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 14px; margin-bottom: 12px; page-break-inside: avoid;">
      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #282A36; padding-bottom: 8px; margin-bottom: 8px;">
        <div>
          <strong style="color: #ffffff; font-size: 14px; font-family: 'Lexend', sans-serif;">${c.name}</strong>
          <span style="background: #282A36; color: #FFB800; font-family: monospace; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; margin-left: 8px;">${c.role}</span>
        </div>
        <span style="background: ${c.provenance === 'CANON' ? '#064E3B' : '#1E3A8A'}; color: ${c.provenance === 'CANON' ? '#34D399' : '#93C5FD'}; font-family: monospace; font-size: 9px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">
          ${c.provenance}
        </span>
      </div>
      <div style="font-size: 12px; color: #D1D5DB; margin-bottom: 6px;">
        <strong style="color: #9CA3AF;">Archetype:</strong> ${c.archetype}
      </div>
      <div style="font-size: 12px; color: #D1D5DB; margin-bottom: 6px;">
        <strong style="color: #9CA3AF;">Motivation:</strong> ${c.coreMotivation}
      </div>
      <div style="font-size: 12px; color: #D1D5DB; margin-bottom: 6px;">
        <strong style="color: #9CA3AF;">Fatal Flaw:</strong> ${c.fatalFlaw}
      </div>
      ${c.signatureDialogue && c.signatureDialogue !== 'NOT_SPECIFIED' ? `
        <div style="background: #0D0E12; border-left: 3px solid ${accent}; padding: 6px 10px; margin: 6px 0; font-style: italic; font-size: 11px; color: #F3F4F6;">
          "${c.signatureDialogue}"
        </div>
      ` : ''}
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; font-size: 11px; color: #9CA3AF;">
        <div><strong style="color: #D1D5DB;">Visual/Wardrobe:</strong> ${c.visualKey}</div>
        <div><strong style="color: #D1D5DB;">Dialect:</strong> ${c.dialectGuidance}</div>
      </div>
    </div>
  `).join("");

  const locationsHtml = data.locationBible.map((loc) => `
    <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 12px; margin-bottom: 10px; page-break-inside: avoid;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <strong style="color: #fff; font-size: 13px; font-family: 'Lexend', sans-serif;">${loc.locationName}</strong>
        <span style="background: #1E3A8A; color: #93C5FD; font-family: monospace; font-size: 9px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">${loc.provenance}</span>
      </div>
      <div style="font-size: 11px; color: #9CA3AF;">
        <div><strong style="color: #D1D5DB;">Type:</strong> ${loc.settingType}</div>
        <div><strong style="color: #D1D5DB;">Spatial Layout:</strong> ${loc.spatialLayout}</div>
        <div><strong style="color: #D1D5DB;">Lighting:</strong> ${loc.lightingConditions}</div>
      </div>
    </div>
  `).join("");

  const worldRulesHtml = data.worldRules.map((r, i) => `
    <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; font-size: 12px; page-break-inside: avoid;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <span style="color: #FFB800; font-family: monospace; font-weight: bold; font-size: 10px;">RULE ${i + 1} (${r.ruleKey})</span>
        <span style="background: #064E3B; color: #34D399; font-family: monospace; font-size: 9px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">${r.provenance}</span>
      </div>
      <div style="color: #F3F4F6; font-weight: 500;">${r.lawDescription}</div>
      <div style="color: #9CA3AF; font-size: 11px; margin-top: 2px;">Impact: ${r.narrativeImpact}</div>
    </div>
  `).join("");

  // Episode 1 Specimen
  const ep = data.episodePackSpecimen;
  const epBeatsHtml = ep ? ep.beats.map((b) => `
    <div style="background: #15161E; border: 1px solid #282A36; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; page-break-inside: avoid;">
      <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; margin-bottom: 4px;">
        <strong style="color: #fff;">Beat ${b.beatNumber}: ${b.label}</strong>
        <span style="color: #FFB800; font-family: monospace;">${b.timestamps}</span>
      </div>
      <p style="margin: 0; font-size: 12px; color: #D1D5DB;">${b.actionSummary}</p>
    </div>
  `).join("") : "";

  const dialogueLinesHtml = ep ? ep.fiveTracks.track2Dialogue.lines.map((d) => `
    <div style="background: #0D0E12; border: 1px solid #282A36; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; font-size: 11px; page-break-inside: avoid;">
      <div style="display: flex; justify-content: space-between; color: #9CA3AF; margin-bottom: 2px;">
        <strong style="color: #fff;">${d.speaker} (${d.timestamp_s}s)</strong>
        <span>Tone: ${d.delivery_tone}</span>
      </div>
      <div style="color: #FFB800; font-style: italic;">"${d.line}"</div>
      <div style="color: #6B7280; font-size: 10px; margin-top: 2px;">Subtext: ${d.subtext}</div>
    </div>
  `).join("") : "";

  printWin.document.write(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>${data.titleIdentity.title} — Production Document (${meta.document_id})</title>
      <link href="https://fonts.googleapis.com/css2?family=Lexend:wght@400;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
      <style>
        * { box-sizing: border-box; }
        body {
          margin: 0;
          padding: 0;
          background: #090A0F;
          color: #E5E7EB;
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }
        .action-bar {
          background: #14151B;
          border-bottom: 1px solid #282A36;
          color: white;
          padding: 12px 24px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          position: sticky;
          top: 0;
          z-index: 1000;
          box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        .print-btn {
          background: ${accent};
          color: #fff;
          border: none;
          padding: 8px 18px;
          font-family: 'Lexend', sans-serif;
          font-weight: 700;
          font-size: 12px;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: filter 0.2s;
        }
        .print-btn:hover { filter: brightness(1.15); }
        .doc-wrapper {
          max-width: 960px;
          margin: 30px auto;
          background: #0E0F15;
          border: 1px solid #282A36;
          border-radius: 12px;
          padding: 40px 48px;
          box-shadow: 0 10px 40px rgba(0,0,0,0.6);
        }
        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 2px solid #282A36;
          padding-bottom: 8px;
          margin-top: 32px;
          margin-bottom: 16px;
          page-break-after: avoid;
        }
        .section-title {
          font-family: 'Lexend', sans-serif;
          font-size: 16px;
          font-weight: 800;
          color: #ffffff;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .section-title span.badge {
          background: ${accent}22;
          color: ${accent};
          font-size: 11px;
          padding: 2px 8px;
          border-radius: 4px;
          border: 1px solid ${accent}44;
        }
        .meta-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
          background: #14151B;
          border: 1px solid #282A36;
          border-radius: 8px;
          padding: 14px;
          margin-bottom: 24px;
          font-size: 11px;
          font-family: monospace;
        }
        .meta-item { display: flex; flex-direction: column; }
        .meta-item .label { color: #6B7280; font-size: 9px; text-transform: uppercase; margin-bottom: 2px; }
        .meta-item .value { color: #E5E7EB; font-weight: bold; }
        .track-box {
          background: #15161E;
          border: 1px solid #282A36;
          border-radius: 8px;
          padding: 14px;
          margin-bottom: 14px;
          page-break-inside: avoid;
        }
        @media print {
          @page {
            size: A4 portrait;
            margin: 10mm 10mm 15mm 10mm;
          }
          .action-bar { display: none !important; }
          body { background: #090A0F !important; }
          .doc-wrapper {
            margin: 0 !important;
            padding: 0 !important;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            max-width: 100% !important;
            width: 100% !important;
          }
          .page-break {
            page-break-before: always;
          }
        }
      </style>
    </head>
    <body>
      <div class="action-bar">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-family: 'Lexend'; font-weight: 800; font-size: 13px; color: ${accent};">WELELE™ PRINT EXPORT</span>
          <span style="color: #6B7280; font-size: 12px;">|</span>
          <span style="font-size: 12px; font-weight: 600;">${meta.document_type}</span>
          <span style="background: #282A36; font-family: monospace; font-size: 10px; padding: 2px 6px; border-radius: 4px;">${meta.document_id}</span>
        </div>
        <button class="print-btn" onclick="window.print()">
          Save / Print Document (PDF)
        </button>
      </div>

      <div class="doc-wrapper">
        <!-- Title Banner & Document Header -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid ${accent}; padding-bottom: 20px; margin-bottom: 20px;">
          <div>
            <span style="color: ${accent}; font-family: 'Lexend'; font-weight: 800; font-size: 11px; letter-spacing: 2px; text-transform: uppercase;">
              ${meta.output_class} // CANONICAL SPECIFICATION
            </span>
            <h1 style="font-family: 'Lexend'; font-size: 30px; font-weight: 900; margin: 4px 0 6px; color: #fff;">
              ${data.titleIdentity.title}
            </h1>
            <p style="margin: 0; font-size: 13px; color: #9CA3AF;">
              ${data.creativeDna.genre} • ${data.titleIdentity.format} (${data.titleIdentity.durationSeconds}s) • ${data.titleIdentity.primaryLanguage}
            </p>
          </div>
          <div style="text-align: right;">
            <div style="font-family: 'Lexend'; font-weight: 800; font-size: 14px; color: #fff;">${studioName}</div>
            <div style="font-size: 11px; color: #9CA3AF; margin-top: 2px;">${studioTagline}</div>
          </div>
        </div>

        <!-- Document Metadata Provenance Banner -->
        <div class="meta-grid">
          <div class="meta-item">
            <span class="label">Document ID</span>
            <span class="value" style="color: ${accent};">${meta.document_id}</span>
          </div>
          <div class="meta-item">
            <span class="label">Source Entity</span>
            <span class="value">${meta.source_entity} (${meta.source_version})</span>
          </div>
          <div class="meta-item">
            <span class="label">Configuration ID</span>
            <span class="value" style="color: #34D399;">${meta.forge_configuration_id || 'CFG-001'}</span>
          </div>
          <div class="meta-item">
            <span class="label">Generated At</span>
            <span class="value">${new Date(meta.generated_at).toLocaleString()}</span>
          </div>
          <div class="meta-item" style="grid-column: span 4; border-top: 1px solid #282A36; padding-top: 6px; margin-top: 4px;">
            <span class="label">Lineage Hash (SHA-256)</span>
            <span class="value" style="font-size: 10px; color: #9CA3AF; word-break: break-all;">${meta.lineage_hash || 'f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6'}</span>
          </div>
        </div>

        <!-- 1. Creative DNA & Dramatic Engine -->
        <div class="section-header" style="margin-top: 16px;">
          <div class="section-title">
            <span>1. Creative DNA & Dramatic Engine</span>
            <span class="badge">CANON</span>
          </div>
        </div>
        <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
          <div style="font-size: 11px; color: #9CA3AF; text-transform: uppercase; font-weight: bold; margin-bottom: 4px;">Logline</div>
          <p style="margin: 0 0 12px; font-size: 13px; color: #F3F4F6; line-height: 1.5; font-style: italic;">"${data.creativeDna.logline}"</p>
          <div style="font-size: 11px; color: #9CA3AF; text-transform: uppercase; font-weight: bold; margin-bottom: 4px;">Dramatic Engine</div>
          <p style="margin: 0; font-size: 12px; color: #D1D5DB; line-height: 1.5;">${data.creativeDna.dramaticEngine}</p>
        </div>

        <!-- 2. Character Production Bible -->
        <div class="section-header">
          <div class="section-title">
            <span>2. Character Production Bible (${data.characterBible.length} Roles)</span>
            <span class="badge">CANON + DERIVED</span>
          </div>
        </div>
        <div>
          ${charactersHtml}
        </div>

        <!-- 3. World & Inviolable Rules -->
        <div class="section-header">
          <div class="section-title">
            <span>3. World Lore & Inviolable Rules</span>
            <span class="badge">CANON</span>
          </div>
        </div>
        <div>
          ${worldRulesHtml}
        </div>

        <!-- 4. Locations & Stages -->
        <div class="section-header">
          <div class="section-title">
            <span>4. World / Location Blueprint</span>
            <span class="badge">DERIVED</span>
          </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          ${locationsHtml}
        </div>

        <!-- Page Break for Production Specs & Episode 1 -->
        <div class="page-break"></div>

        <!-- 5. Visual & Audio Language -->
        <div class="section-header">
          <div class="section-title">
            <span>5. Technical Production Language</span>
            <span class="badge">${data.visualLanguage.provenance || 'PRODUCTION_DECISION'}</span>
          </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 20px;">
          <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 14px; font-size: 11px;">
            <strong style="color: #fff; display: block; margin-bottom: 8px; font-family: 'Lexend';">Visual Language (${data.visualLanguage.aspectRatio})</strong>
            <div style="color: #9CA3AF; margin-bottom: 4px;"><strong style="color: #D1D5DB;">Lighting Grammar:</strong> ${data.visualLanguage.lightingGrammar}</div>
            <div style="color: #9CA3AF; margin-bottom: 4px;"><strong style="color: #D1D5DB;">LUT:</strong> ${data.visualLanguage.lut}</div>
            <div style="color: #9CA3AF; margin-bottom: 6px;"><strong style="color: #D1D5DB;">Framing:</strong> ${data.visualLanguage.framingProtocols.join('; ')}</div>
            <div style="color: #9CA3AF;"><strong style="color: #D1D5DB;">Lenses:</strong> ${data.visualLanguage.lenses ? data.visualLanguage.lenses.map(l => `${l.lens} (${l.use})`).join(', ') : '24mm, 35mm, 50mm'}</div>
          </div>
          <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 14px; font-size: 11px;">
            <strong style="color: #fff; display: block; margin-bottom: 8px; font-family: 'Lexend';">Audio Language & Foley</strong>
            <div style="color: #9CA3AF; margin-bottom: 4px;"><strong style="color: #D1D5DB;">Score Theme:</strong> ${data.audioLanguage.scoreTheme} (${data.audioLanguage.bpm} BPM)</div>
            <div style="color: #9CA3AF; margin-bottom: 4px;"><strong style="color: #D1D5DB;">Mix Standard:</strong> ${data.audioLanguage.dialogueMix}</div>
            <div style="color: #9CA3AF;"><strong style="color: #D1D5DB;">Foley Events:</strong> ${data.audioLanguage.foleyEvents.map(f => `${f.event} [${f.timing}]`).join(', ') || 'Standard Cues'}</div>
          </div>
        </div>

        <!-- 6. Continuity Spine & Production Constraints -->
        <div class="section-header">
          <div class="section-title">
            <span>6. Continuity Spine & Production Constraints</span>
            <span class="badge">${data.continuityAndConstraints.provenance || 'CANON'}</span>
          </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 20px;">
          <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 14px; font-size: 11px;">
            <strong style="color: #fff; display: block; margin-bottom: 8px; font-family: 'Lexend';">Chronology Spine</strong>
            ${data.continuityAndConstraints.chronologySpine.map(s => `
              <div style="margin-bottom: 6px; border-bottom: 1px dashed #282A36; padding-bottom: 4px;">
                <span style="color: #FFB800; font-weight: bold;">Anchor ${s.anchor_number}: ${s.anchor_name}</span>
                <p style="margin: 2px 0 0; color: #D1D5DB;">${s.summary}</p>
              </div>
            `).join('')}
            <div style="margin-top: 8px;">
              <strong style="color: #fff; display: block; margin-bottom: 4px;">Plants & Payoffs:</strong>
              ${data.continuityAndConstraints.plantsAndPayoffs.map(p => `
                <div style="color: #9CA3AF; font-size: 10px; margin-bottom: 2px;">• <strong style="color: #E5E7EB;">${p.plant}</strong> (${p.status}) → Target: ${p.payoff_target}</div>
              `).join('')}
            </div>
          </div>
          <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 14px; font-size: 11px;">
            <strong style="color: #fff; display: block; margin-bottom: 8px; font-family: 'Lexend';">Production Constraints</strong>
            <div style="color: #9CA3AF; margin-bottom: 4px;"><strong style="color: #D1D5DB;">Budget Tier:</strong> ${data.continuityAndConstraints.budgetTier}</div>
            <div style="color: #9CA3AF; margin-bottom: 4px;"><strong style="color: #D1D5DB;">Max Cast / Scene:</strong> ${data.continuityAndConstraints.maxCastPerScene} characters</div>
            <div style="color: #9CA3AF; margin-bottom: 6px;"><strong style="color: #D1D5DB;">Max Sets:</strong> ${data.continuityAndConstraints.maxSets} physical builds</div>
            <div>
              <strong style="color: #EF4444; display: block; margin-bottom: 4px;">Safety Limits & Protocol:</strong>
              ${data.continuityAndConstraints.safetyLimits.map(s => `<div style="color: #FCA5A5; font-size: 10px; margin-bottom: 2px;">⚠ ${s}</div>`).join('')}
            </div>
          </div>
        </div>

        <!-- 7. Prompt Constitution & Governed Rules -->
        <div class="section-header">
          <div class="section-title">
            <span>7. Governed Prompt Constitution</span>
            <span class="badge">${data.promptConstitution.provenance || 'CANON'}</span>
          </div>
        </div>
        <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 14px; margin-bottom: 24px; font-size: 11px;">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
            <div>
              <strong style="color: #34D399; display: block; margin-bottom: 6px;">Governing Laws:</strong>
              ${data.promptConstitution.governingLaws.map(g => `<div style="color: #D1D5DB; margin-bottom: 3px;">✓ ${g}</div>`).join('')}
            </div>
            <div>
              <strong style="color: #EF4444; display: block; margin-bottom: 6px;">Forbidden Mutations:</strong>
              ${data.promptConstitution.forbiddenMutations.map(m => `<div style="color: #FCA5A5; margin-bottom: 3px;">✕ ${m}</div>`).join('')}
            </div>
          </div>
        </div>

        <!-- Page Break for Episode 1 Production Pack -->
        <div class="page-break"></div>

        ${ep ? `
          <!-- 8. Episode 1 Production Pack Specimen -->
          <div class="section-header">
            <div class="section-title">
              <span>8. Episode 1 Production Pack ("${ep.episodeTitle}")</span>
              <span class="badge">5 COORDINATED TRACKS</span>
            </div>
          </div>

          <div class="track-box">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #282A36; padding-bottom: 6px; margin-bottom: 10px;">
              <strong style="color: #fff; font-size: 12px; font-family: 'Lexend';">Episode Beats & Cliffhanger Cut</strong>
              <span style="color: #FF6500; font-family: monospace; font-size: 11px; font-weight: bold;">Paywall @ 88.0s</span>
            </div>
            ${epBeatsHtml}
            <div style="background: #7F1D1D33; border: 1px solid #EF444455; border-radius: 6px; padding: 8px 12px; font-size: 11px; color: #FCA5A5; margin-top: 8px;">
              <strong>Paywall Cliffhanger:</strong> "${ep.cliffhangerPrompt}"
            </div>
          </div>

          <!-- Coordinated 5 Tracks Breakdown -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <!-- Track 1: Video -->
            <div class="track-box">
              <strong style="color: #fff; font-size: 12px; display: block; margin-bottom: 6px; font-family: 'Lexend';">Track 1: VIDEO (GENERATED)</strong>
              <div style="font-size: 11px; color: #9CA3AF; space-y-2;">
                ${ep.fiveTracks.track1Video.scenes.map(s => `
                  <div style="margin-bottom: 6px; border-bottom: 1px dashed #282A36; padding-bottom: 4px;">
                    <strong style="color: #D1D5DB;">${s.timing}:</strong> ${s.visual_action}
                  </div>
                `).join('')}
              </div>
            </div>

            <!-- Track 2: Dialogue -->
            <div class="track-box">
              <strong style="color: #fff; font-size: 12px; display: block; margin-bottom: 6px; font-family: 'Lexend';">Track 2: DIALOGUE (CANON)</strong>
              ${dialogueLinesHtml}
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 10px;">
            <!-- Track 3: Narration -->
            <div class="track-box">
              <strong style="color: #fff; font-size: 11px; display: block; margin-bottom: 4px; font-family: 'Lexend';">Track 3: NARRATION (DERIVED)</strong>
              <p style="font-size: 11px; color: #D1D5DB; font-style: italic; margin: 0;">"${ep.fiveTracks.track3Narration.openingHook || '—'}"</p>
            </div>

            <!-- Track 4: Ambience -->
            <div class="track-box">
              <strong style="color: #fff; font-size: 11px; display: block; margin-bottom: 4px; font-family: 'Lexend';">Track 4: AMBIENCE (GENERATED)</strong>
              <p style="font-size: 11px; color: #9CA3AF; margin: 0;">${ep.fiveTracks.track4Ambience.roomTone}</p>
            </div>

            <!-- Track 5: Music -->
            <div class="track-box">
              <strong style="color: #fff; font-size: 11px; display: block; margin-bottom: 4px; font-family: 'Lexend';">Track 5: MUSIC (GENERATED)</strong>
              <p style="font-size: 11px; color: #9CA3AF; margin: 0;">${ep.fiveTracks.track5Music.scoreTheme} (${ep.fiveTracks.track5Music.bpm || 68} BPM)</p>
            </div>
          </div>
        ` : ''}

        <!-- Document Footer -->
        <div style="border-top: 1px solid #282A36; padding-top: 16px; margin-top: 40px; display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #6B7280; page-break-inside: avoid;">
          <span>${studioName} • Read-Only Projection Layer</span>
          <span>Canon Overrides Prompt Convenience • Welele Story OS</span>
        </div>
      </div>
    </body>
    </html>
  `);

  printWin.document.close();
  printWin.focus();
}
