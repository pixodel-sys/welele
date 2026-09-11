/**
 * Welele Media™ — Brand Ident Policy Engine (Deterministic Episode-Based Playback)
 * 
 * Invariants:
 * 1. Launch Rule: First episode of session + every 5th subsequent episode (ident_frequency: 5)
 * 2. Episode Exposure Based: Driven strictly by episode starts, completely independent of wall-clock time.
 * 3. Dynamic Duration Discovery: Player discovers physical duration from the loaded media element.
 * 4. Configurable Watchdog Failsafe: watchdogMs = (mediaDuration + failsafeBuffer) * 1000.
 */

import { BrandIdentConfig } from '../types/experience';
import { DEFAULT_BRAND_IDENT_CONFIG } from '../utils/experienceFallback';

export const STORAGE_KEY_EPISODES_SINCE_IDENT = 'welele_episodes_since_ident';

let memoryEpisodesSinceIdent: number | null = null;

/**
 * Retrieve the current session episode count since the last brand ident presentation.
 * Returns `null` if no episode has yet been played in the current session.
 */
export function getEpisodesSinceIdent(): number | null {
  try {
    if (typeof sessionStorage !== 'undefined') {
      const raw = sessionStorage.getItem(STORAGE_KEY_EPISODES_SINCE_IDENT);
      if (raw !== null && raw !== undefined) {
        const parsed = parseInt(raw, 10);
        return isNaN(parsed) ? memoryEpisodesSinceIdent : parsed;
      }
    }
    return memoryEpisodesSinceIdent;
  } catch {
    return memoryEpisodesSinceIdent;
  }
}

/**
 * Persist the episode count since the last brand ident presentation.
 */
export function setEpisodesSinceIdent(count: number): void {
  memoryEpisodesSinceIdent = count;
  try {
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem(STORAGE_KEY_EPISODES_SINCE_IDENT, count.toString());
    }
  } catch (e) {
    console.warn('[BrandIdentPolicy] Storage write failed, retained in memory:', e);
  }
}

/**
 * Reset the session episode counter (used for testing or clean session bootstrap).
 */
export function resetEpisodeIdentCounter(): void {
  memoryEpisodesSinceIdent = null;
  try {
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.removeItem(STORAGE_KEY_EPISODES_SINCE_IDENT);
    }
  } catch {
    // Ignore storage clear errors
  }
}

/**
 * Deterministically evaluates whether the Brand Ident should play before an episode.
 * 
 * - If play_brand_ident is false: Returns false.
 * - If first episode of session (count === null): Returns true, sets count to 0.
 * - For subsequent episodes: Increments count by 1.
 *   - If count >= ident_frequency: Returns true, resets count to 0.
 *   - Otherwise: Returns false, saves updated count.
 */
export function evaluateEpisodeIdentTrigger(
  config: BrandIdentConfig = DEFAULT_BRAND_IDENT_CONFIG
): boolean {
  if (!config.play_brand_ident) {
    return false;
  }

  const frequency = Math.max(1, config.ident_frequency ?? 5);
  const currentCount = getEpisodesSinceIdent();

  // First episode of session -> Present brand ident ritual
  if (currentCount === null) {
    setEpisodesSinceIdent(0);
    return true;
  }

  // Subsequent episode entry
  const nextCount = currentCount + 1;
  if (nextCount >= frequency) {
    // Satisfied frequency cycle (e.g. 5th subsequent episode) -> Present ident & reset
    setEpisodesSinceIdent(0);
    return true;
  } else {
    // Intermediate episode -> Skip ident & update counter
    setEpisodesSinceIdent(nextCount);
    return false;
  }
}

/**
 * Dynamically computes the failsafe watchdog timeout in milliseconds based on
 * the actual physical duration of the loaded media asset + the configurable safety buffer.
 * 
 * Watchdog formula: (actualDurationSeconds + failsafeBufferSeconds) * 1000
 */
export function computeWatchdogMs(
  mediaDurationSeconds?: number | null,
  failsafeBufferSeconds: number = 1.0,
  fallbackDurationSeconds: number = 5.2
): number {
  const duration =
    mediaDurationSeconds && mediaDurationSeconds > 0
      ? mediaDurationSeconds
      : fallbackDurationSeconds;
  const buffer = failsafeBufferSeconds >= 0 ? failsafeBufferSeconds : 1.0;
  return Math.round((duration + buffer) * 1000);
}
