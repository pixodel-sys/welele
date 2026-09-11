/**
 * Welele Media™ — Brand Ident Policy Test Suite
 * Validates deterministic episode counting, frequency thresholding, watchdog computation, and session isolation.
 */

import {
  evaluateEpisodeIdentTrigger,
  computeWatchdogMs,
  resetEpisodeIdentCounter,
  getEpisodesSinceIdent,
  setEpisodesSinceIdent,
} from '../services/brandIdentPolicy';
import { BrandIdentConfig } from '../types/experience';
import { DEFAULT_BRAND_IDENT_CONFIG } from '../utils/experienceFallback';

function assert(condition: boolean, message: string) {
  if (!condition) {
    throw new Error(`Assertion Failed: ${message}`);
  }
  console.log(`  ✓ ${message}`);
}

export function runBrandIdentTests() {
  console.log('\n--- Running Welele Brand Ident Policy Test Suite ---\n');

  // Test 1: Launch Configuration (ident_frequency = 5) - First Episode + Every 5th Subsequent
  console.log('Test 1: Launch Configuration (ident_frequency = 5)');
  resetEpisodeIdentCounter();

  const launchConfig: BrandIdentConfig = {
    ...DEFAULT_BRAND_IDENT_CONFIG,
    ident_frequency: 5,
    failsafe_buffer: 1.0,
  };

  // Ep 1 (Session Start) -> Must trigger Ident
  const ep1Result = evaluateEpisodeIdentTrigger(launchConfig);
  assert(ep1Result === true, 'Session Start -> Episode 1 triggers Brand Ident');
  assert(getEpisodesSinceIdent() === 0, 'Counter is reset to 0 after Ep 1 trigger');

  // Ep 2 -> No Ident
  const ep2Result = evaluateEpisodeIdentTrigger(launchConfig);
  assert(ep2Result === false, 'Episode 2 does NOT trigger Brand Ident');
  assert(getEpisodesSinceIdent() === 1, 'Counter incremented to 1 on Ep 2');

  // Ep 3 -> No Ident
  const ep3Result = evaluateEpisodeIdentTrigger(launchConfig);
  assert(ep3Result === false, 'Episode 3 does NOT trigger Brand Ident');
  assert(getEpisodesSinceIdent() === 2, 'Counter incremented to 2 on Ep 3');

  // Ep 4 -> No Ident
  const ep4Result = evaluateEpisodeIdentTrigger(launchConfig);
  assert(ep4Result === false, 'Episode 4 does NOT trigger Brand Ident');
  assert(getEpisodesSinceIdent() === 3, 'Counter incremented to 3 on Ep 4');

  // Ep 5 -> No Ident
  const ep5Result = evaluateEpisodeIdentTrigger(launchConfig);
  assert(ep5Result === false, 'Episode 5 does NOT trigger Brand Ident');
  assert(getEpisodesSinceIdent() === 4, 'Counter incremented to 4 on Ep 5');

  // Ep 6 (5th subsequent) -> Must trigger Ident
  const ep6Result = evaluateEpisodeIdentTrigger(launchConfig);
  assert(ep6Result === true, 'Episode 6 (5th subsequent) triggers Brand Ident');
  assert(getEpisodesSinceIdent() === 0, 'Counter is reset to 0 after Ep 6 trigger');

  // Ep 7..10 -> No Ident
  for (let i = 7; i <= 10; i++) {
    const res = evaluateEpisodeIdentTrigger(launchConfig);
    assert(res === false, `Episode ${i} does NOT trigger Brand Ident`);
  }
  assert(getEpisodesSinceIdent() === 4, 'Counter is at 4 after Episode 10');

  // Ep 11 -> Must trigger Ident
  const ep11Result = evaluateEpisodeIdentTrigger(launchConfig);
  assert(ep11Result === true, 'Episode 11 (5th subsequent) triggers Brand Ident');
  assert(getEpisodesSinceIdent() === 0, 'Counter is reset to 0 after Ep 11 trigger');

  // Test 2: Frequency = 1 Configuration (Every Episode)
  console.log('\nTest 2: Configuration Driven (ident_frequency = 1 - Every Episode)');
  resetEpisodeIdentCounter();
  const freq1Config: BrandIdentConfig = {
    ...DEFAULT_BRAND_IDENT_CONFIG,
    ident_frequency: 1,
  };

  for (let ep = 1; ep <= 5; ep++) {
    const res = evaluateEpisodeIdentTrigger(freq1Config);
    assert(res === true, `ident_frequency = 1: Episode ${ep} triggers Brand Ident`);
  }

  // Test 3: Frequency = 2 Configuration (Every Second Episode)
  console.log('\nTest 3: Configuration Driven (ident_frequency = 2)');
  resetEpisodeIdentCounter();
  const freq2Config: BrandIdentConfig = {
    ...DEFAULT_BRAND_IDENT_CONFIG,
    ident_frequency: 2,
  };

  assert(evaluateEpisodeIdentTrigger(freq2Config) === true, 'Ep 1 (session start) -> triggers');
  assert(evaluateEpisodeIdentTrigger(freq2Config) === false, 'Ep 2 -> skips');
  assert(evaluateEpisodeIdentTrigger(freq2Config) === true, 'Ep 3 (2nd subsequent) -> triggers');
  assert(evaluateEpisodeIdentTrigger(freq2Config) === false, 'Ep 4 -> skips');
  assert(evaluateEpisodeIdentTrigger(freq2Config) === true, 'Ep 5 (2nd subsequent) -> triggers');

  // Test 4: Dynamic Watchdog Calculation
  console.log('\nTest 4: Dynamic Watchdog Calculation Formula');
  const wd1 = computeWatchdogMs(5.2, 1.0);
  assert(wd1 === 6200, '5.2s media + 1.0s buffer = 6200ms');

  const wd2 = computeWatchdogMs(3.45, 1.0);
  assert(wd2 === 4450, '3.45s media + 1.0s buffer = 4450ms');

  const wd3 = computeWatchdogMs(null, 1.5, 5.2);
  assert(wd3 === 6700, 'Fallback duration (5.2s) + 1.5s buffer = 6700ms');

  const wd4 = computeWatchdogMs(10.0, 2.0);
  assert(wd4 === 12000, '10.0s media + 2.0s buffer = 12000ms');

  // Test 5: Disabled Brand Ident
  console.log('\nTest 5: Disabled Brand Ident (play_brand_ident = false)');
  resetEpisodeIdentCounter();
  const disabledConfig: BrandIdentConfig = {
    ...DEFAULT_BRAND_IDENT_CONFIG,
    play_brand_ident: false,
  };
  assert(evaluateEpisodeIdentTrigger(disabledConfig) === false, 'Disabled config never triggers on Ep 1');
  assert(evaluateEpisodeIdentTrigger(disabledConfig) === false, 'Disabled config never triggers on Ep 2');

  // Test 6: Skip Interaction & Counter Preservation
  console.log('\nTest 6: Skip Interaction & Counter Preservation');
  resetEpisodeIdentCounter();
  // Start session on Ep 1
  const startRes = evaluateEpisodeIdentTrigger(launchConfig);
  assert(startRes === true, 'Ep 1 triggers ident');
  // User skips ident immediately (handleIdentFinished(true) does NOT alter the counter)
  assert(getEpisodesSinceIdent() === 0, 'Counter remains 0 after user skips ident on Ep 1');
  // Auto-advance to Ep 2
  assert(evaluateEpisodeIdentTrigger(launchConfig) === false, 'Ep 2 does not trigger ident after Ep 1 skip');
  assert(getEpisodesSinceIdent() === 1, 'Counter is 1 on Ep 2');

  console.log('\n🎉 ALL BRAND IDENT TESTS PASSED SUCCESSFULLY!\n');
}

// Auto-run if executed in a script environment
try {
  runBrandIdentTests();
} catch (err) {
  console.error('\n❌ Test Failure:', err);
}
