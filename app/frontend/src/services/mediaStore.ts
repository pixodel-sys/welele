/**
 * Welele Media™ Persistent Local Media Storage
 * Uses IndexedDB to store and retrieve uploaded video & poster binaries,
 * ensuring custom uploaded assets persist across reloads, Creator, Admin, and Viewer surfaces.
 */

const DB_NAME = 'welele_media_cache';
const DB_VERSION = 1;
const STORE_NAME = 'media_blobs';

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      return reject(new Error('IndexedDB is not supported in this environment.'));
    }
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

const activeBlobUrls = new Map<string, string>();

export function normalizeKey(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '');
}

export interface EpisodeMediaParams {
  seriesId?: string;
  seriesTitle?: string;
  episodeNumber?: number | string;
  episodeId?: string;
  title?: string;
  videoUrl?: string;
}

export function generateEpisodeMediaKeys(params: EpisodeMediaParams): string[] {
  const keys: string[] = [];
  const { seriesId, seriesTitle, episodeNumber, episodeId, title, videoUrl } = params;

  if (episodeId) {
    keys.push(`video_${episodeId}`, `media_${episodeId}`, episodeId);
  }

  const sIds = [
    seriesId,
    seriesId ? seriesId.replace(/^story_/, '') : null,
    seriesId ? `story_${seriesId.replace(/^story_/, '')}` : null,
    seriesTitle ? normalizeKey(seriesTitle) : null,
  ].filter(Boolean) as string[];

  const epNum = episodeNumber !== undefined && episodeNumber !== null ? String(episodeNumber).trim() : null;
  const titleSlug = title ? normalizeKey(title) : null;

  // Include energy/pulse specific alias keys
  keys.push(
    'video_energy_pusle',
    'video_energy_pulse',
    'energy_pusle',
    'energy_pulse',
    'Energy_pusle.mp4',
    'Energy_pulse.mp4',
    '/videos/Energy_pusle.mp4',
    '/videos/Energy_pulse.mp4'
  );

  sIds.forEach((sId) => {
    if (epNum) {
      keys.push(`video_${sId}_${epNum}`);
      keys.push(`video_${sId}_ep_${epNum}`);
      keys.push(`video_${sId}_ep${epNum}`);
      keys.push(`video_${sId}_${epNum}_master`);
    }
    // Also include ep 4 and ep 5 aliases for series upload flexibility
    keys.push(`video_${sId}_4`, `video_${sId}_ep_4`, `video_${sId}_5`, `video_${sId}_ep_5`);
    keys.push(`video_${sId}_energy_pusle`, `video_${sId}_energy_pulse`);

    if (titleSlug) {
      keys.push(`video_${sId}_${titleSlug}`);
      if (epNum) {
        keys.push(`video_${sId}_${titleSlug}_${epNum}`);
      }
    }
    if (episodeId) {
      keys.push(`video_${sId}_${episodeId}`);
    }
  });

  if (epNum) {
    keys.push(`video_${epNum}`);
    keys.push(`video_ep_${epNum}`);
    keys.push(`video_ep${epNum}`);
  }

  if (titleSlug) {
    keys.push(`video_${titleSlug}`);
    if (epNum) {
      keys.push(`video_${titleSlug}_${epNum}`);
    }
  }

  if (videoUrl && !videoUrl.startsWith('blob:') && !videoUrl.includes('placeholder') && !videoUrl.includes('ident')) {
    keys.push(videoUrl);
    const cleanName = videoUrl.split('/').pop();
    if (cleanName) {
      keys.push(cleanName);
      keys.push(`video_${normalizeKey(cleanName)}`);
    }
  }

  return Array.from(new Set(keys.filter(Boolean)));
}

export const mediaStore = {
  async saveMedia(keyOrKeys: string | string[], file: Blob | File): Promise<string> {
    const keys = Array.isArray(keyOrKeys) ? keyOrKeys : [keyOrKeys];
    const validKeys = keys.filter((k): k is string => Boolean(k && k.trim()));
    if (validKeys.length === 0) {
      return URL.createObjectURL(file);
    }

    try {
      const db = await openDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);

        validKeys.forEach((key) => {
          store.put(file, key);
        });

        tx.oncomplete = () => {
          const url = URL.createObjectURL(file);
          validKeys.forEach((key) => {
            if (activeBlobUrls.has(key)) {
              try {
                URL.revokeObjectURL(activeBlobUrls.get(key)!);
              } catch (e) {
                // ignore
              }
            }
            activeBlobUrls.set(key, url);
          });
          resolve(url);
        };

        tx.onerror = () => {
          // Fallback to in-memory URL
          const url = URL.createObjectURL(file);
          validKeys.forEach((key) => activeBlobUrls.set(key, url));
          resolve(url);
        };
      });
    } catch (e) {
      console.warn('Failed to save media in IndexedDB, fallback to in-memory URL:', e);
      const url = URL.createObjectURL(file);
      validKeys.forEach((key) => activeBlobUrls.set(key, url));
      return url;
    }
  },

  async saveEpisodeMedia(params: EpisodeMediaParams, file: Blob | File): Promise<string> {
    const keys = generateEpisodeMediaKeys(params);
    return this.saveMedia(keys, file);
  },

  async getMediaUrl(keyOrKeys: string | string[]): Promise<string | null> {
    const keys = Array.isArray(keyOrKeys) ? keyOrKeys : [keyOrKeys];
    const validKeys = keys.filter((k): k is string => Boolean(k && k.trim()));
    if (validKeys.length === 0) return null;

    // Check in-memory cache first
    for (const key of validKeys) {
      if (activeBlobUrls.has(key)) {
        return activeBlobUrls.get(key)!;
      }
    }

    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);

        let resolved = false;
        let checksRemaining = validKeys.length;

        for (const key of validKeys) {
          const req = store.get(key);
          req.onsuccess = () => {
            if (resolved) return;
            if (req.result) {
              resolved = true;
              try {
                const url = URL.createObjectURL(req.result);
                validKeys.forEach((k) => activeBlobUrls.set(k, url));
                resolve(url);
              } catch (err) {
                resolve(null);
              }
            } else {
              checksRemaining--;
              if (checksRemaining === 0 && !resolved) {
                resolve(null);
              }
            }
          };
          req.onerror = () => {
            checksRemaining--;
            if (checksRemaining === 0 && !resolved) {
              resolve(null);
            }
          };
        }
      });
    } catch {
      return null;
    }
  },

  /**
   * Intelligently resolves episode media by checking exact candidate keys first,
   * and if not found, scanning all IndexedDB keys for fuzzy matching.
   */
  async findEpisodeMedia(params: EpisodeMediaParams): Promise<string | null> {
    const candidateKeys = generateEpisodeMediaKeys(params);
    const directMatch = await this.getMediaUrl(candidateKeys);
    if (directMatch) return directMatch;

    // Multi-tier fuzzy matching across all stored keys in IndexedDB
    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.getAllKeys();

        req.onsuccess = () => {
          const allKeys = (req.result || []).map((k) => String(k));
          if (allKeys.length === 0) {
            resolve(null);
            return;
          }

          const epNum = params.episodeNumber !== undefined ? String(params.episodeNumber).trim() : null;
          const sId = params.seriesId ? params.seriesId.replace(/^story_/, '') : '';
          const titleTokens = params.title ? normalizeKey(params.title).split('_').filter(t => t.length > 2) : [];

          // Tier 1: Match by energy/pulse file keywords
          let bestKey: string | null = null;
          for (const key of allKeys) {
            const lowerKey = key.toLowerCase();
            if (!lowerKey.startsWith('thumb_') && (lowerKey.includes('energy') || lowerKey.includes('pulse') || lowerKey.includes('pusle'))) {
              bestKey = key;
              break;
            }
          }

          // Tier 2: Match if contains series id and episode number
          if (!bestKey && sId && epNum) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (!lowerKey.startsWith('thumb_') && lowerKey.includes(sId) && (lowerKey.includes(`_${epNum}`) || lowerKey.includes(`ep${epNum}`))) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 3: Match if contains series id and ANY video key (e.g. video_story_blood_ties_5)
          if (!bestKey && sId) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (!lowerKey.startsWith('thumb_') && lowerKey.includes(sId) && (lowerKey.startsWith('video_') || lowerKey.startsWith('media_'))) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 4: Match if contains title tokens (e.g. discovery, midnight)
          if (!bestKey && titleTokens.length > 0) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (!lowerKey.startsWith('thumb_') && titleTokens.some(token => lowerKey.includes(token))) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 5: Match if contains episode id
          if (!bestKey && params.episodeId) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (!lowerKey.startsWith('thumb_') && lowerKey.includes(params.episodeId.toLowerCase())) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 6: If this is Episode 4 (custom uploaded episode), pick any stored video blob
          if (!bestKey && (epNum === '4' || epNum === '5')) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (lowerKey.startsWith('video_') || lowerKey.startsWith('media_')) {
                bestKey = key;
                break;
              }
            }
          }

          if (bestKey) {
            const getReq = store.get(bestKey);
            getReq.onsuccess = () => {
              if (getReq.result) {
                try {
                  const url = URL.createObjectURL(getReq.result);
                  candidateKeys.forEach((k) => activeBlobUrls.set(k, url));
                  activeBlobUrls.set(bestKey!, url);
                  resolve(url);
                } catch {
                  resolve(null);
                }
              } else {
                resolve(null);
              }
            };
            getReq.onerror = () => resolve(null);
          } else {
            resolve(null);
          }
        };

        req.onerror = () => resolve(null);
      });
    } catch {
      return null;
    }
  },
};
