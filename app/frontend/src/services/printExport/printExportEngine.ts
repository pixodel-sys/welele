/**
 * Welele Media™ — Print Export Engine v1.0 (Projection Layer)
 * Read-only presentation layer projecting canonical Welele state into printable artifacts.
 * Establishes three output classes:
 *   1. Production Documents (Story Package, Production Bible, Episode Production Pack, Production Reports)
 *   2. Executive / Business Reports (Production status, project reports, IP reports)
 *   3. Presentation Decks (Pitch decks, title decks, episode decks)
 */

import {
  OutputClass,
  DocumentType,
  DocumentMetadata,
  PrintableProductionReportData
} from "./printExport.types";
import { renderAndOpenProductionReport } from "./renderProductionReport";

export class PrintExportEngine {
  /**
   * Generates document metadata maintaining strict provenance and lineage tracking.
   */
  public static createDocumentMetadata(
    documentType: DocumentType,
    outputClass: OutputClass,
    sourceEntity: string,
    sourceVersion: string = "v1.0.0",
    forgeConfigId: string = "CFG-001",
    lineageHash?: string
  ): DocumentMetadata {
    const docIdPrefix = {
      [OutputClass.PRODUCTION_DOCUMENT]: "DOC-PROD",
      [OutputClass.EXECUTIVE_REPORT]: "DOC-EXEC",
      [OutputClass.PRESENTATION_DECK]: "DOC-DECK"
    }[outputClass];

    const randomSuffix = Math.random().toString(36).substring(2, 8).toUpperCase();
    return {
      document_id: `${docIdPrefix}-${randomSuffix}`,
      document_type: documentType,
      output_class: outputClass,
      source_entity: sourceEntity,
      source_version: sourceVersion,
      generated_at: new Date().toISOString(),
      generated_by: "Welele_Print_Export_Engine_v1.0",
      forge_configuration_id: forgeConfigId,
      lineage_hash: lineageHash || "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6"
    };
  }

  /**
   * Output Class 1: Production Documents
   * Projects canonical Story Package + Production Bible + Episode Pack into printable report.
   */
  public static exportProductionReportFromCanonical(
    packageData: any,
    bibleData?: any,
    episodePackData?: any
  ): void {
    const title = packageData.package_title || packageData.ip_title || "Untitled Project";
    const franchiseCode = packageData.franchise_code || "IP-ASSET";
    const cfgId = packageData.forge_configuration_id || bibleData?.forge_configuration_id || "CFG-001";
    const lineageHash = packageData.lineage_hash || bibleData?.lineage_hash || "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6";

    const metadata = this.createDocumentMetadata(
      "PRODUCTION_REPORT",
      OutputClass.PRODUCTION_DOCUMENT,
      `${franchiseCode} (${title})`,
      bibleData?.version || "1.0.0",
      cfgId,
      lineageHash
    );

    // Build complete report data payload from canonical state
    const reportPayload: PrintableProductionReportData = {
      metadata,
      brand: {
        studioName: "WELELE MEDIA™",
        studioTagline: "The Story OS for African Cinema",
        accentColor: "#FF6500"
      },
      titleIdentity: {
        title: title,
        franchiseCode: franchiseCode,
        format: bibleData?.section_1_title_identity?.format || "9:16 Vertical Microdrama",
        durationSeconds: packageData.target_duration_seconds || 90,
        primaryLanguage: packageData.primary_language || "isiZulu",
        secondaryLanguages: ["English", "Sesotho", "Tsotsitaal"]
      },
      creativeDna: {
        logline: packageData.logline || "A high-stakes African vertical microdrama.",
        thematicPremise: bibleData?.section_2_creative_dna?.thematic_premise || "Customary royal birthright versus corporate mining commodification.",
        genre: packageData.genre || "Vertical Microdrama",
        tonalAnchors: ["Township Realism", "High-Stakes Melodrama", "Ancestral Inviolability"],
        dramaticEngine: bibleData?.section_2_creative_dna?.dramatic_engine || "A Soweto midwife protecting a royal infant against a mining patriarch seeking to seize the child."
      },
      characterBible: (bibleData?.section_3_character_bible || [
        {
          name: "Thandiwe Sithole",
          role: "PROTAGONIST",
          archetype: "The Devout Midwife / Moral Shield",
          coreMotivation: "Protect the royal infant from corporate exploitation and redeem her estranged daughter.",
          fatalFlaw: "Rigid moral pride.",
          signatureDialogue: "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa.",
          visualKey: "Weathered green clinic coat over traditional Zulu floral dress.",
          wardrobePalette: "Earthy Ochre & Medical White",
          costumeDistressRules: "Delivery sweat and candle wax.",
          castingSpec: "Female, 50-55, commanding resonance.",
          dialectGuidance: "Formal ancestral isiZulu",
          provenance: "CANON"
        },
        {
          name: "Bhekisisa Khumalo",
          role: "ANTAGONIST",
          archetype: "The Dynastic Mining Patriarch",
          coreMotivation: "Secure an authentic male heir to retain ancestral mining concessions.",
          fatalFlaw: "Belief that sacred birthright can be bought with cash.",
          signatureDialogue: "That child carries the only bloodline that keeps my mining shafts open. Hand him over.",
          visualKey: "Bespoke charcoal three-piece suit, gold signet ring.",
          wardrobePalette: "Sandton Steel Gray, Black Silk & 18k Gold Accents",
          costumeDistressRules: "Immaculate ironed crease.",
          castingSpec: "Male, 55-60, imposing stature.",
          dialectGuidance: "Corporate Sandton isiZulu with English legal terms.",
          provenance: "CANON"
        },
        {
          name: "Lerato Sithole",
          role: "SUPPORTING",
          archetype: "The Desperate Surrogate Daughter",
          coreMotivation: "Escape loan shark debt and protect her newborn.",
          fatalFlaw: "Impulsive vulnerability to financial shortcuts.",
          signatureDialogue: "Mama, forgive me... I had no other way to clear the loan sharks.",
          visualKey: "Oversized dark coat, postpartum exhaustion.",
          wardrobePalette: "Faded Black Thrifted Coat & Hospital Wristband",
          costumeDistressRules: "Hospital ID band visible on wrist.",
          castingSpec: "Female, 22-26, emotional vulnerability.",
          dialectGuidance: "Soweto urban isiZulu.",
          provenance: "CANON"
        }
      ]),
      locationBible: (bibleData?.section_4_location_bible || [
        {
          locationName: "Mofolo South Clinic Delivery Ward",
          settingType: "Practical Interior / Soundstage Build",
          spatialLayout: "15m² practical room: weathered green walls, metal gurney, wooden cabinet.",
          lightingConditions: "2700K Warm candle flame key contrasted against deep shadows.",
          criteria: "Soundstage build preferred for controlled flame rigging.",
          provenance: "DERIVED"
        },
        {
          locationName: "Clinic Exterior Gate & Alley",
          settingType: "Practical Exterior Dawn",
          spatialLayout: "Corrugated iron perimeter fence, dusty township alley.",
          lightingConditions: "5600K Pre-dawn ambient light sliced by vehicle headlights.",
          criteria: "Practical location scouting in Soweto.",
          provenance: "DERIVED"
        }
      ]),
      worldRules: (bibleData?.section_5_world_rules || [
        {
          ruleKey: "RULE_CUSTOMARY_LINEAGE",
          lawDescription: "Customary Zulu royal lineage covenants supersede commercial surrogacy contracts under customary law.",
          narrativeImpact: "Invalidates commercial claims when royal ink-mark is identified.",
          provenance: "CANON"
        },
        {
          ruleKey: "RULE_MINING_LEASE_CONDITIONALITY",
          lawDescription: "Mining concessions remain valid only while verified direct royal bloodline is maintained.",
          narrativeImpact: "If Bhekisisa loses custody, concessions revert to tribal trust.",
          provenance: "CANON"
        },
        {
          ruleKey: "RULE_1912_SEAL_AUTHORITY",
          lawDescription: "A birth entered into customary clinic ledger with 1912 seal triggers provincial land registry freeze.",
          narrativeImpact: "Provides legal customary protection for Thandiwe.",
          provenance: "CANON"
        }
      ]),
      visualLanguage: {
        aspectRatio: "9:16 Vertical (1080x1920 Native)",
        framingProtocols: [
          "Single-character vertical headroom discipline (top 15% clear for HUD).",
          "Vertical over-the-shoulder confrontation with compressed depth of field.",
          "Tight vertical Dutch angles on power shifts."
        ],
        lightingGrammar: "Chiaroscuro: 2700K candle key interior contrasted against 5600K exterior headlights.",
        colorPalette: [
          { color_name: "Township Ochre", hex: "#FF6500", meaning: "Ancestral sanctuary & warmth" },
          { color_name: "Royal Ochre Ink", hex: "#FFA000", meaning: "Customary birthmark & covenant" },
          { color_name: "Corporate Gray", hex: "#4A5568", meaning: "Sandton mining power" }
        ],
        lut: "Welele_Mzansi_Chiaroscuro_v1",
        lenses: [
          { lens: "24mm f/1.8 Wide", use: "Exterior convoy confrontation" },
          { lens: "35mm f/1.4 Prime", use: "Two-character vertical dialogue" },
          { lens: "50mm f/1.2 Macro", use: "Extreme close-up on birthmark" }
        ],
        provenance: "PRODUCTION_DECISION"
      },
      audioLanguage: {
        vernacularMatrix: {
          "Thandiwe": "Formal ancestral isiZulu",
          "Bhekisisa": "Corporate Sandton isiZulu",
          "Lerato": "Contemporary Soweto street isiZulu"
        },
        foleyEvents: [
          { event: "Rolling Blackout Silence", timing: "00:00-00:10", description: "Township silence with newborn cry." },
          { event: "Convoy Diesel Rumble", timing: "00:15-00:30", description: "V8 diesel engine rumble on gravel." },
          { event: "Briefcase Snap", timing: "00:45", description: "Metallic latch snap opening cash." },
          { event: "Racking 9mm Slide", timing: "00:85-00:88", description: "Heavy slide of 9mm pistols." }
        ],
        scoreTheme: "The Ancestral Heartbeat",
        bpm: 68,
        dialogueMix: "-14 LUFS Mobile Phone Optimized",
        provenance: "PRODUCTION_DECISION"
      },
      continuityAndConstraints: {
        chronologySpine: [
          { anchor_number: 1, anchor_name: "Midnight Delivery", summary: "Thandiwe delivers baby by candlelight; spots royal birthmark." },
          { anchor_number: 2, anchor_name: "Dawn Arrival", summary: "Bhekisisa arrives with cash; Lerato confesses." },
          { anchor_number: 3, anchor_name: "Threshold Stand", summary: "Thandiwe refuses settlement; community forms protective barrier." }
        ],
        plantsAndPayoffs: [
          { plant: "Royal Ink-Mark on infant shoulder", status: "PLANTED", payoff_target: "Ep 1 & Season Finale" },
          { plant: "1912 Land Covenant Seal in safe", status: "PLANTED", payoff_target: "Ep 3 & Climax" }
        ],
        budgetTier: "Welele Microdrama Tier 1",
        maxCastPerScene: 3,
        maxSets: 2,
        safetyLimits: ["Zero live ammunition", "Medical prosthetic newborn", "Flame marshal on set"],
        provenance: "CANON"
      },
      promptConstitution: {
        governingLaws: [
          "CANON OVERRIDES PROMPT CONVENIENCE",
          "NO SILENT CANON CREATION",
          "STRICT 9:16 VERTICAL NATIVE",
          "VERNACULAR INTEGRITY"
        ],
        forbiddenMutations: [
          "Changing Thandiwe's role from devout midwife to broker",
          "Allowing Bhekisisa to claim child without customary process",
          "Removing the 88s cliffhanger paywall cut"
        ],
        aspectRatioRule: "9:16 Vertical Native Only",
        canonOverrideRule: "CANON_OVERRIDES_PROMPT_CONVENIENCE",
        provenance: "CANON"
      },
      episodePackSpecimen: {
        episodeNumber: 1,
        episodeTitle: "The Midnight Sovereign",
        durationSeconds: 88,
        storyBrief: "During a Soweto rolling blackout, midwife Thandiwe delivers a child bearing a legendary royal birthmark. At dawn, Sandton mining tycoon Bhekisisa Khumalo arrives to claim the child, revealing Thandiwe's estranged daughter Lerato as the surrogate.",
        cliffhangerPrompt: "Will Thandiwe sign the Khumalo settlement or trigger a township uprising to protect the royal infant?",
        beats: [
          {
            beatNumber: 1,
            label: "Cold Open: Midnight Delivery & Ink-Mark",
            timestamps: "00:00 - 00:15",
            intensity: 8,
            actionSummary: "Midwife Thandiwe delivers newborn by candlelight during blackout; spots royal ink-mark on infant shoulder.",
            cliffhanger: false,
            provenance: "CANON"
          },
          {
            beatNumber: 2,
            label: "Dawn Escalation: The Khumalo Convoy",
            timestamps: "00:15 - 00:50",
            intensity: 9,
            actionSummary: "At dawn, Bhekisisa Khumalo arrives with cash briefcases. Lerato confesses to surrogacy contract.",
            cliffhanger: false,
            provenance: "CANON"
          },
          {
            beatNumber: 3,
            label: "Climax Stand-off & Paywall Cut",
            timestamps: "00:50 - 00:88",
            intensity: 10,
            actionSummary: "Guards draw weapons. Township neighbours surround clinic with sjamboks as Thandiwe raises customary ledger. Hard cut at 88s.",
            cliffhanger: true,
            provenance: "CANON"
          }
        ],
        fiveTracks: {
          track1Video: {
            scenes: [
              { scene_id: "SC_01", timing: "00:00 - 00:15", visual_action: "Tight vertical close-up on Thandiwe's brow; camera tilts to royal birthmark glowing under amber flame.", framing: "9:16 Close-Up", lighting: "2700K Candle Key" },
              { scene_id: "SC_02", timing: "00:15 - 00:50", visual_action: "Low-angle Dutch shot of Mercedes convoy; Bhekisisa steps out in charcoal suit; Lerato crying.", framing: "9:16 Low-Angle", lighting: "5600K Pre-dawn Blue Ambient" },
              { scene_id: "SC_03", timing: "00:50 - 00:88", visual_action: "Guards rack 9mm handguns; community emerges with sjamboks; Thandiwe raises customary ledger.", framing: "9:16 Whip-Pan & Freeze", lighting: "High-contrast Golden Sunrise" }
            ],
            lightingExecution: "Chiaroscuro key separation",
            provenance: "GENERATED"
          },
          track2Dialogue: {
            lines: [
              { speaker: "Thandiwe", line: "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa.", subtext: "Maternal moral defiance", timestamp_s: 35, delivery_tone: "Steely maternal authority" },
              { speaker: "Bhekisisa", line: "That child carries the only bloodline that keeps my mining shafts open. Hand him over.", subtext: "Dynastic survival panic", timestamp_s: 55, delivery_tone: "Cold measured authority" },
              { speaker: "Lerato", line: "Mama, forgive me... I had no other way to clear the loan sharks.", subtext: "Shattered guilt", timestamp_s: 72, delivery_tone: "Choked, tearful" }
            ],
            provenance: "CANON"
          },
          track3Narration: {
            hasNarration: true,
            openingHook: "In Soweto, blood is thicker than gold... but at dawn, gold came to collect.",
            monologues: [{ character: "Thandiwe", vo_line: "(Silent prayer) Nkosi yam... not this bloodline. Not in my clinic." }],
            provenance: "DERIVED"
          },
          track4Ambience: {
            roomTone: "Rolling blackout room tone with newborn cry and distant generator hum.",
            foley: [
              { timestamp_s: 5, foley: "Newborn sharp gasp" },
              { timestamp_s: 18, foley: "Gravel road convoy crunch" },
              { timestamp_s: 42, foley: "Aluminum briefcase double-click" },
              { timestamp_s: 84, foley: "9mm handgun slide racking" }
            ],
            provenance: "GENERATED"
          },
          track5Music: {
            scoreTheme: "The Sacred Bloodline (Isibusiso Main Motif)",
            bpm: 68,
            stems: [
              { time: "00:00 - 00:15", stem: "Solo Zulu drum heartbeat at 68 BPM" },
              { time: "00:15 - 00:50", stem: "Staccato cello enters building tension" },
              { time: "00:50 - 00:87", stem: "String tremolo & brass crescendo" },
              { time: "00:88", stem: "Abrupt cut to absolute silence at paywall" }
            ],
            paywallCut: "ABRUPT_SILENCE_AT_CLIFFHANGER",
            provenance: "GENERATED"
          }
        }
      }
    };

    renderAndOpenProductionReport(reportPayload);
  }

  /**
   * Output Class 2: Executive / Business Reports
   * Projects production status, project milestone reports, and financial reports.
   */
  public static exportExecutiveReport(data: import("./printExport.types").ProductionReportData): void {
    const printWin = window.open("", "_blank");
    if (!printWin) {
      alert("Please allow popups to export the Welele Executive Report.");
      return;
    }

    const studioName = data.brand.studioName || "WELELE MEDIA™";
    const accent = data.brand.accentColor || "#FF6500";
    const meta = data.metadata || this.createDocumentMetadata(
      "PRODUCTION_STATUS_REPORT",
      OutputClass.EXECUTIVE_REPORT,
      data.projectReference || data.reportTitle,
      "v1.0.0"
    );

    const metricsHtml = data.kpiMetrics.map((m) => `
      <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 16px;">
        <span style="font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: #9CA3AF; display: block; margin-bottom: 6px;">${m.label}</span>
        <span style="font-family: 'Lexend', sans-serif; font-weight: 800; font-size: 22px; color: #fff; display: block;">${m.value}</span>
        ${m.changeOrNote ? `<span style="font-size: 11px; color: ${accent}; font-weight: 600; margin-top: 4px; display: block;">${m.changeOrNote}</span>` : ""}
      </div>
    `).join("");

    const deliverablesHtml = data.deliverables.map((item) => `
      <tr style="border-bottom: 1px solid #241e33; font-size: 12px;">
        <td style="padding: 10px 12px; font-weight: 600; color: #fff;">${item.title}</td>
        <td style="padding: 10px 12px; color: #a1a1aa;">${item.category}</td>
        <td style="padding: 10px 12px;">
          <span style="background: ${item.status === 'Completed' ? '#064E3B' : '#1E3A8A'}; color: ${item.status === 'Completed' ? '#34D399' : '#93C5FD'}; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; font-family: monospace;">
            ${item.status}
          </span>
        </td>
        <td style="padding: 10px 12px; color: #a1a1aa; font-family: monospace;">${item.dueDate || "—"}</td>
        <td style="padding: 10px 12px; color: #d4d4d8;">${item.assignee || "Unassigned"}</td>
      </tr>
    `).join("");

    printWin.document.write(`
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>${data.reportTitle} — Executive Report (${meta.document_id})</title>
        <link href="https://fonts.googleapis.com/css2?family=Lexend:wght@400;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
          * { box-sizing: border-box; }
          body {
            margin: 0;
            padding: 0;
            background: #090A0F;
            color: #E5E7EB;
            font-family: 'Inter', system-ui, sans-serif;
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
            z-index: 100;
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
          }
          .report-container {
            max-width: 920px;
            margin: 30px auto;
            background: #0E0F15;
            border: 1px solid #282A36;
            border-radius: 12px;
            padding: 40px 48px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.6);
          }
          .meta-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            background: #14151B;
            border: 1px solid #282A36;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 24px;
            font-size: 11px;
            font-family: monospace;
          }
          .meta-item { display: flex; flex-direction: column; }
          .meta-item .label { color: #6B7280; font-size: 9px; text-transform: uppercase; margin-bottom: 2px; }
          .meta-item .value { color: #E5E7EB; font-weight: bold; }
          @media print {
            @page { size: A4 portrait; margin: 10mm; }
            .action-bar { display: none !important; }
            body { background: #090A0F; }
            .report-container { margin: 0; border: none; padding: 0; width: 100%; max-width: 100%; }
          }
        </style>
      </head>
      <body>
        <div class="action-bar">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-family: 'Lexend'; font-weight: 800; font-size: 13px; color: ${accent};">${studioName}</span>
            <span style="color: #6B7280; font-size: 12px;">|</span>
            <span style="font-size: 12px; font-weight: 600;">${meta.document_type}</span>
            <span style="background: #282A36; font-family: monospace; font-size: 10px; padding: 2px 6px; border-radius: 4px;">${meta.document_id}</span>
          </div>
          <button class="print-btn" onclick="window.print()">Print / Save PDF</button>
        </div>

        <div class="report-container">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #282A36; padding-bottom: 20px; margin-bottom: 20px;">
            <div>
              <span style="color: ${accent}; font-family: 'Lexend'; font-weight: 800; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase;">
                ${meta.output_class} // EXECUTIVE BRIEFING
              </span>
              <h1 style="font-family: 'Lexend'; font-size: 28px; font-weight: 900; margin: 4px 0 0; color: #fff;">${data.reportTitle}</h1>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 10px; color: #6B7280; text-transform: uppercase;">Reference</div>
              <div style="font-family: 'Lexend'; font-weight: 700; color: #fff; font-size: 13px;">${data.projectReference}</div>
              <div style="font-size: 11px; color: #9CA3AF; margin-top: 2px;">${data.reportDate}</div>
            </div>
          </div>

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
              <span class="label">Prepared By</span>
              <span class="value">${data.preparedBy}</span>
            </div>
            <div class="meta-item">
              <span class="label">Generated At</span>
              <span class="value">${new Date(meta.generated_at).toLocaleString()}</span>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 28px;">
            ${metricsHtml}
          </div>

          <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 18px; margin-bottom: 28px;">
            <h3 style="font-family: 'Lexend'; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: ${accent}; margin: 0 0 6px;">Executive Summary</h3>
            <p style="font-size: 13px; line-height: 1.6; color: #D1D5DB; margin: 0;">${data.executiveSummary}</p>
          </div>

          <h3 style="font-family: 'Lexend'; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: #fff; margin-bottom: 10px;">Deliverables & Milestone Progress</h3>
          <table style="width: 100%; border-collapse: collapse; text-align: left; margin-bottom: 28px;">
            <thead>
              <tr style="border-bottom: 2px solid #282A36; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #6B7280;">
                <th style="padding: 8px 12px;">Item / Deliverable</th>
                <th style="padding: 8px 12px;">Track</th>
                <th style="padding: 8px 12px;">Status</th>
                <th style="padding: 8px 12px;">Target Date</th>
                <th style="padding: 8px 12px;">Lead</th>
              </tr>
            </thead>
            <tbody>
              ${deliverablesHtml}
            </tbody>
          </table>

          ${data.budgetSummary ? `
            <div style="background: #15161E; border: 1px solid #282A36; border-radius: 8px; padding: 16px; margin-bottom: 28px;">
              <h3 style="font-family: 'Lexend'; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #34D399; margin: 0 0 10px;">Financial Summary</h3>
              <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; font-size: 12px;">
                <div><span style="color: #6B7280;">Budget Total:</span> <strong style="color: #fff;">${data.budgetSummary.currencySymbol || '$'}${data.budgetSummary.budgetTotal.toLocaleString()}</strong></div>
                <div><span style="color: #6B7280;">Spend to Date:</span> <strong style="color: #fff;">${data.budgetSummary.currencySymbol || '$'}${data.budgetSummary.spendToDate.toLocaleString()}</strong></div>
                <div><span style="color: #6B7280;">Variance:</span> <strong style="color: ${data.budgetSummary.variance >= 0 ? '#34D399' : '#EF4444'};">${data.budgetSummary.variance >= 0 ? '+' : ''}${data.budgetSummary.variance}%</strong></div>
              </div>
            </div>
          ` : ''}
        </div>
      </body>
      </html>
    `);
    printWin.document.close();
    printWin.focus();
  }

  /**
   * Output Class 3: Presentation Decks
   * Projects pitch decks, title decks, and investor presentation materials.
   */
  public static exportPitchDeck(data: import("./printExport.types").ProductionScriptDeckData): void {
    const printWin = window.open("", "_blank");
    if (!printWin) {
      alert("Please allow popups to export the Welele Pitch Deck.");
      return;
    }

    const studioName = data.brand.studioName || "WELELE MEDIA™";
    const studioTagline = data.brand.studioTagline || "The Story OS for African Cinema";
    const accent = data.brand.accentColor || "#FF6500";
    const meta = data.metadata || this.createDocumentMetadata(
      "PITCH_DECK",
      OutputClass.PRESENTATION_DECK,
      data.projectTitle,
      data.episodeOrVersion || "v1.0"
    );

    const formattedDate = new Date(data.date).toLocaleDateString("en-ZA", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });

    const sceneSlidesHtml = data.scenes.map((scene, idx) => {
      const sceneNumFormatted = String(scene.sceneNumber).padStart(2, "0");
      const visualContent = scene.storyboardImageUrl
        ? `<div style="position: relative; border-radius: 10px; overflow: hidden; border: 1px solid #282A36; background: #090A0F; max-height: 360px; display: flex; align-items: center; justify-content: center;">
             <img src="${scene.storyboardImageUrl}" style="max-width: 100%; max-height: 360px; object-fit: contain;" />
           </div>`
        : `<div style="height: 240px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #14151B; border: 2px dashed #282A36; border-radius: 10px; color: #6B7280;">
             <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Storyboard / Visual Direction</span>
           </div>`;

      return `
        <div class="slide">
          <header class="slide-header">
            <div class="slide-tag">SCENE ${sceneNumFormatted} // PRODUCTION SPEC</div>
            <div class="slide-brand">${studioName} · ${meta.document_id}</div>
          </header>

          <div class="scene-grid">
            <div class="scene-visual-col">
              ${visualContent}
              ${scene.locationNotes ? `
                <div class="meta-card" style="margin-top: 12px;">
                  <span class="meta-label">Location / Setup</span>
                  <span class="meta-value">${scene.locationNotes}</span>
                </div>
              ` : ""}
            </div>

            <div class="scene-detail-col">
              <h2 class="slugline">${scene.slugline}</h2>
              <p class="scene-summary">${scene.summary}</p>

              ${scene.visualCues ? `
                <div class="cue-box">
                  <span class="cue-title">Visual & Camera Direction</span>
                  <p class="cue-text">${scene.visualCues}</p>
                </div>
              ` : ""}

              ${scene.dialoguePreview ? `
                <div class="dialogue-box">
                  <span class="cue-title">Key Dialogue</span>
                  <p class="dialogue-text">${scene.dialoguePreview}</p>
                </div>
              ` : ""}

              <div class="meta-row">
                ${scene.estimatedDurationSeconds ? `
                  <div class="meta-chip">
                    <span class="chip-label">Est. Duration</span>
                    <span class="chip-val">${scene.estimatedDurationSeconds}s</span>
                  </div>
                ` : ""}
                ${scene.characters && scene.characters.length > 0 ? `
                  <div class="meta-chip">
                    <span class="chip-label">Cast</span>
                    <span class="chip-val">${scene.characters.join(", ")}</span>
                  </div>
                ` : ""}
              </div>
            </div>
          </div>

          <footer class="slide-footer">
            <span>${data.projectTitle} · ${data.episodeOrVersion || "Production Master"}</span>
            <span>Slide ${idx + 2} of ${data.scenes.length + 1}</span>
          </footer>
        </div>
      `;
    }).join("");

    printWin.document.write(`
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>${data.projectTitle} — Pitch Deck (${meta.document_id})</title>
        <link href="https://fonts.googleapis.com/css2?family=Lexend:wght@400;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
          * { box-sizing: border-box; }
          body {
            margin: 0;
            padding: 0;
            background: #090A0F;
            color: #E5E7EB;
            font-family: 'Inter', system-ui, sans-serif;
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
            color: white;
            border: none;
            padding: 8px 18px;
            font-family: 'Lexend', sans-serif;
            font-weight: 700;
            font-size: 12px;
            border-radius: 6px;
            cursor: pointer;
          }
          .slide {
            width: 100%;
            max-width: 1080px;
            min-height: 85vh;
            margin: 30px auto;
            background: #0E0F15;
            border: 1px solid #282A36;
            border-radius: 16px;
            padding: 40px 50px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 15px 40px rgba(0,0,0,0.5);
          }
          .slide-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #282A36;
            padding-bottom: 12px;
            margin-bottom: 24px;
          }
          .slide-tag {
            font-family: 'Lexend', sans-serif;
            font-weight: 800;
            font-size: 12px;
            letter-spacing: 2px;
            color: ${accent};
          }
          .slide-brand {
            font-size: 11px;
            color: #6B7280;
            text-transform: uppercase;
            font-weight: 600;
            font-family: monospace;
          }
          .slide-footer {
            display: flex;
            justify-content: space-between;
            border-top: 1px solid #282A36;
            padding-top: 12px;
            margin-top: 24px;
            font-size: 11px;
            color: #6B7280;
          }
          .cover-title {
            font-family: 'Lexend', sans-serif;
            font-size: 42px;
            font-weight: 900;
            line-height: 1.1;
            color: #ffffff;
            margin: 0 0 14px;
          }
          .cover-logline {
            font-size: 16px;
            line-height: 1.6;
            color: #9CA3AF;
            max-width: 800px;
            margin-bottom: 30px;
          }
          .cover-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
          }
          .meta-card {
            background: #14151B;
            border: 1px solid #282A36;
            border-radius: 8px;
            padding: 14px;
          }
          .meta-label {
            display: block;
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #6B7280;
            margin-bottom: 4px;
          }
          .meta-value {
            font-family: 'Lexend', sans-serif;
            font-weight: 700;
            font-size: 14px;
            color: #fff;
          }
          .scene-grid {
            display: grid;
            grid-template-columns: 1fr 1.2fr;
            gap: 30px;
            align-items: start;
          }
          .slugline {
            font-family: 'Lexend', sans-serif;
            font-size: 20px;
            font-weight: 800;
            color: #ffffff;
            margin: 0 0 10px;
          }
          .scene-summary {
            font-size: 13px;
            line-height: 1.6;
            color: #D1D5DB;
            margin-bottom: 16px;
          }
          .cue-box {
            background: #14151B;
            border-left: 3px solid ${accent};
            border-radius: 4px;
            padding: 10px 14px;
            margin-bottom: 12px;
          }
          .cue-title {
            font-family: 'Lexend', sans-serif;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: ${accent};
            display: block;
            margin-bottom: 2px;
          }
          .cue-text { margin: 0; font-size: 12px; color: #E5E7EB; line-height: 1.5; }
          .dialogue-box {
            background: #14151B;
            border: 1px solid #282A36;
            border-radius: 4px;
            padding: 10px 14px;
            margin-bottom: 12px;
          }
          .dialogue-text { margin: 0; font-style: italic; font-size: 12px; color: #F3F4F6; line-height: 1.5; }
          .meta-row { display: flex; gap: 10px; flex-wrap: wrap; }
          .meta-chip {
            background: #1F212D;
            border-radius: 16px;
            padding: 4px 12px;
            display: flex;
            gap: 6px;
            font-size: 11px;
          }
          .chip-label { color: #9CA3AF; }
          .chip-val { font-weight: 600; color: #fff; }
          @media print {
            @page { size: A4 landscape; margin: 10mm; }
            .action-bar { display: none !important; }
            body { background: #090A0F !important; }
            .slide {
              box-shadow: none !important;
              margin: 0 !important;
              width: 100% !important;
              max-width: 100% !important;
              min-height: 100vh !important;
              border-radius: 0 !important;
              border: none !important;
              page-break-before: always;
              padding: 15mm 15mm;
            }
            .slide:first-of-type { page-break-before: avoid; }
          }
        </style>
      </head>
      <body>
        <div class="action-bar">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-family: 'Lexend'; font-weight: 800; font-size: 13px; color: ${accent};">${studioName}</span>
            <span style="color: #6B7280; font-size: 12px;">|</span>
            <span style="font-size: 12px; font-weight: 600;">${meta.document_type}</span>
            <span style="background: #282A36; font-family: monospace; font-size: 10px; padding: 2px 6px; border-radius: 4px;">${meta.document_id}</span>
          </div>
          <button class="print-btn" onclick="window.print()">Print / Save PDF</button>
        </div>

        <!-- Slide 01: Cover -->
        <div class="slide">
          <header class="slide-header">
            <div class="slide-tag">${meta.output_class} // PITCH SPECIFICATION</div>
            <div class="slide-brand">${studioName} · ${meta.document_id}</div>
          </header>

          <div style="margin: auto 0;">
            <h1 class="cover-title">${data.projectTitle}</h1>
            ${data.logline ? `<p class="cover-logline">${data.logline}</p>` : ""}

            <div class="cover-grid">
              <div class="meta-card">
                <span class="meta-label">Client / Entity</span>
                <span class="meta-value">${data.clientOrClientProject || "Welele Original"}</span>
              </div>
              <div class="meta-card">
                <span class="meta-label">Director / Writer</span>
                <span class="meta-value">${data.authorOrDirector || "Production Team"}</span>
              </div>
              <div class="meta-card">
                <span class="meta-label">Date & Version</span>
                <span class="meta-value">${formattedDate} · ${data.episodeOrVersion || "v1.0"}</span>
              </div>
            </div>
          </div>

          <footer class="slide-footer">
            <span>${studioName} · ${studioTagline}</span>
            <span>Document ID: ${meta.document_id} · Source: ${meta.source_entity}</span>
          </footer>
        </div>

        <!-- Slide 02+: Scenes -->
        ${sceneSlidesHtml}
      </body>
      </html>
    `);
    printWin.document.close();
    printWin.focus();
  }
}
