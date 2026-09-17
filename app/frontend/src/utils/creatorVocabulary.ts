import { CurrentAction, StoryState, ForgeCompletionAssessment } from '../types/storyForge';

export interface CreatorVocabularyEntry {
  internalTerm: string;
  creatorTerm: string;
  definition: string;
}

export const CREATOR_VOCABULARY: Record<string, string> = {
  'Dependency': 'Something still to be decided',
  'Required state deficiency': 'Missing story detail',
  'Counterforce': "What's standing in the way?",
  'Knowledge state': 'What does this character know?',
  'Validation': 'Story consistency check',
  'Propagation': 'Checking what this changes',
  'Canon': 'Established story',
  'Production decision': 'Production choice',
  'Mutations': 'Story updates',
  'Invariants': 'Essential story requirements',
};

export interface CreatorStageInfo {
  stageNumber: number;
  totalStages: number;
  name: string;
  tagline: string;
  description: string;
  isCurrent: boolean;
  isSatisfied: boolean;
  milestoneCode: string;
}

/**
 * Maps existing M0–M3 engine milestones onto the 5 creator-facing stages.
 * This is strictly a presentation translation layer; it does not alter engine invariants.
 */
export function getCreatorStages(
  assessment: ForgeCompletionAssessment | null,
  currentAction: CurrentAction | null,
  eventsCount: number = 0
): { stages: CreatorStageInfo[]; currentStageNumber: number; progressPercent: number } {
  const satisfied = assessment?.satisfied_milestones || [];
  const currentM = assessment?.current_milestone;
  const isComplete = assessment?.status === 'FORGE_COMPLETE' || currentM === 'FORGE_COMPLETE';

  const isM0Satisfied = satisfied.includes('PREMISE_LOCK') || isComplete || currentM === 'DRAMATIC_ENGINE_LOCK' || currentM === 'EPISODIC_ARC_LOCK';
  const isM1Satisfied = satisfied.includes('DRAMATIC_ENGINE_LOCK') || isComplete || currentM === 'EPISODIC_ARC_LOCK';
  const isM2Satisfied = (satisfied.includes('EPISODIC_ARC_LOCK') || eventsCount >= 6) || isComplete;
  const isM3Satisfied = isComplete;

  let currentStageNumber = 1;
  if (isM3Satisfied) {
    currentStageNumber = 5;
  } else if (isM2Satisfied) {
    currentStageNumber = 4;
  } else if (isM1Satisfied) {
    currentStageNumber = 3;
  } else if (isM0Satisfied) {
    currentStageNumber = 2;
  } else {
    currentStageNumber = 1;
  }

  const stages: CreatorStageInfo[] = [
    {
      stageNumber: 1,
      totalStages: 5,
      name: 'Foundation',
      tagline: "Let's establish your story.",
      description: 'Establish the premise, protagonist, story objective and creative/production context.',
      isCurrent: currentStageNumber === 1,
      isSatisfied: isM0Satisfied,
      milestoneCode: 'PREMISE_LOCK',
    },
    {
      stageNumber: 2,
      totalStages: 5,
      name: 'Core Story',
      tagline: "Let's understand the people and the conflict.",
      description: 'Characters, motivations, counterforce, relationships, stakes and central dilemma.',
      isCurrent: currentStageNumber === 2,
      isSatisfied: isM1Satisfied,
      milestoneCode: 'DRAMATIC_ENGINE_LOCK',
    },
    {
      stageNumber: 3,
      totalStages: 5,
      name: 'Story Arc',
      tagline: "Let's build the dramatic journey.",
      description: 'Major turning points, revelations, escalation, climax, resolution and continuity.',
      isCurrent: currentStageNumber === 3,
      isSatisfied: isM2Satisfied,
      milestoneCode: 'EPISODIC_ARC_LOCK',
    },
    {
      stageNumber: 4,
      totalStages: 5,
      name: 'Episode Structure',
      tagline: "Let's shape the story for the format.",
      description: 'Translate the established story into high-tension microdrama episodes and cliffhangers.',
      isCurrent: currentStageNumber === 4,
      isSatisfied: isM3Satisfied,
      milestoneCode: 'EPISODIC_SHAPING',
    },
    {
      stageNumber: 5,
      totalStages: 5,
      name: 'Forge Complete',
      tagline: 'Your story has been forged.',
      description: 'Terminal creator-facing state: your certified Story Package is complete.',
      isCurrent: currentStageNumber === 5,
      isSatisfied: isM3Satisfied,
      milestoneCode: 'FORGE_COMPLETE',
    },
  ];

  // Calculate honest percentage based on milestone progression + spine depth
  let progressPercent = 15;
  if (isM3Satisfied) {
    progressPercent = 100;
  } else if (isM2Satisfied) {
    progressPercent = 80;
  } else if (isM1Satisfied) {
    const anchorRatio = Math.min(eventsCount, 6) / 6;
    progressPercent = Math.round(50 + anchorRatio * 25);
  } else if (isM0Satisfied) {
    progressPercent = 35;
  }

  return { stages, currentStageNumber, progressPercent };
}

export interface TranslatedQuestion {
  headline: string;
  context: string;
  whyItMatters: string;
  inputPlaceholder: string;
  category: string;
  behindTheScenes: {
    internalDependency: string;
    deficiencyDescription: string;
    skill: string;
  };
}

/**
 * Translates raw engine dependency keys and prompt requests into clear,
 * inspiring, human-centered creative decisions with zero specimen contamination.
 */
export function translateCreatorQuestion(
  action: CurrentAction | null,
  storyState: StoryState | null
): TranslatedQuestion {
  const rawKey = action?.active_dependency_key || '';
  const rawQuestion = action?.question || '';
  const rawProposal = action?.proposal || '';
  const rawDesc = action?.active_dependency_description || '';
  const skill = action?.skill || 'EXCAVATOR';

  // Default fallback (targeted to dependency, zero generic "What's next?")
  let headline = rawQuestion || (rawDesc ? `Regarding ${rawDesc.replace(/\.$/, '')}: How does this develop?` : 'Shape this dramatic story element.');
  let context = 'Help shape this creative turning point.';
  let whyItMatters = 'Your decisions define the core character dynamics and emotional stakes.';
  let inputPlaceholder = 'Describe what happens, who is involved, and what changes...';
  let category = 'Story Development';

  // 1. Counterforce / Antagonist / Obstacle
  if (
    rawKey.includes('COUNTERFORCE') ||
    rawKey.includes('ANTAGONIST') ||
    rawDesc.toLowerCase().includes('opposing force') ||
    rawDesc.toLowerCase().includes('counterforce')
  ) {
    headline = "What's standing in your protagonist's way?";
    context = "We understand what your protagonist wants. Now we need to understand the main force preventing them from getting it.";
    whyItMatters = "Drama lives in resistance. An active counterforce — whether a rival, an unyielding system, or personal adversary — gives your story its central tension.";
    inputPlaceholder = 'e.g. A relentless creditor, an estranged business partner, a community elder, or a corrupt official...';
    category = 'Conflict & Counterforce';
  }
  // 2. Protagonist Definition & Motivation
  else if (
    rawKey.includes('PROTAGONIST') ||
    rawKey.includes('MOTIVATION') ||
    rawDesc.toLowerCase().includes('motivation')
  ) {
    headline = "What is driving your protagonist?";
    context = "Every strong story is powered by a character who wants something specific and urgent.";
    whyItMatters = "When the audience knows what your lead character desperately wants or fears losing, every scene carries immediate emotional weight.";
    inputPlaceholder = 'e.g. They need to clear their family name before the deadline, protect their child, or secure an urgent contract...';
    category = 'Protagonist Drive';
  }
  // 3. Relational Dynamic / Interpersonal Leverage
  else if (
    rawKey.includes('RELATIONSHIP') ||
    rawKey.includes('DYNAMIC') ||
    rawDesc.toLowerCase().includes('relational')
  ) {
    headline = "What is the tension between your key characters?";
    context = "Explore the emotional friction, hidden secrets, or shared history connecting these people.";
    whyItMatters = "Dynamic relationships keep scenes unpredictable. Shared history and conflicting agendas turn simple conversations into battlegrounds.";
    inputPlaceholder = 'e.g. They used to be close allies, but one holds leverage over the other regarding a past mistake...';
    category = 'Relationships & Friction';
  }
  // 4. Chronology / Story Arc Turning Points
  else if (
    rawKey.includes('CHRONOLOGY') ||
    rawKey.includes('ANCHOR') ||
    rawDesc.toLowerCase().includes('chronology') ||
    rawDesc.toLowerCase().includes('turning point')
  ) {
    headline = "What dramatic turning point escalates the stakes?";
    context = "Advance the narrative journey with a concrete event that changes the situation for your characters.";
    whyItMatters = "Microdramas thrive on constant cause and effect. Each turning point forces your protagonist to adapt and make harder choices.";
    inputPlaceholder = 'e.g. A surprise visitor reveals an ultimatum, forcing the protagonist into an uneasy alliance...';
    category = 'Story Progression';
  }
  // 5. World Rules / Setting Boundaries
  else if (
    rawKey.includes('WORLD') ||
    rawKey.includes('RULE') ||
    rawDesc.toLowerCase().includes('world rules')
  ) {
    headline = "What are the rules and boundaries of this world?";
    context = "Establish the consequences, cultural traditions, or physical realities that govern your setting.";
    whyItMatters = "Clear rules keep the stakes grounded and believable, ensuring victories and failures feel earned.";
    inputPlaceholder = 'e.g. Strict customary protocols forbid speaking out of turn, or corporate compliance penalties are fatal to the firm...';
    category = 'World & Setting';
  }
  // 6. Narrative Plant / Hidden Secret
  else if (
    rawKey.includes('PLANT') ||
    rawKey.includes('SECRET') ||
    rawDesc.toLowerCase().includes('plant') ||
    rawDesc.toLowerCase().includes('payoff')
  ) {
    headline = "What physical clue or secret enters the story?";
    context = "Anchor a tangible object, concealed truth, or ticking clock that will pay off later.";
    whyItMatters = "A physical seed planted early rewards viewer attention when it resurfaces during the climax.";
    inputPlaceholder = 'e.g. An unopened letter, a misplaced set of keys, a recorded voice memo, or an altered contract...';
    category = 'Props & Secrets';
  }
  // 7. Production Choices
  else if (
    rawKey.includes('PRODUCTION') ||
    rawDesc.toLowerCase().includes('production')
  ) {
    headline = "What are your practical production choices?";
    context = "Frame the physical staging, filming constraints, or location choices for this story.";
    whyItMatters = "Aligning creative ambition with production reality ensures the story can be filmed efficiently without sacrificing dramatic impact.";
    inputPlaceholder = 'e.g. Confined single-room dialogue, night exterior, minimal cast in tight close-ups...';
    category = 'Production Choices';
  }

  // If the backend already provided a well-formed question that is natural human language,
  // we respect its core prompt while elevating the framing
  if (rawQuestion && !rawQuestion.toUpperCase().includes('RESOLVE DEPENDENCY')) {
    headline = rawQuestion;
  }

  return {
    headline,
    context: rawProposal ? `Candidate direction: "${rawProposal}"` : context,
    whyItMatters,
    inputPlaceholder,
    category,
    behindTheScenes: {
      internalDependency: rawKey || 'Story Continuity & Depth',
      deficiencyDescription: rawDesc || 'Refining narrative completeness and emotional resonance.',
      skill,
    },
  };
}
