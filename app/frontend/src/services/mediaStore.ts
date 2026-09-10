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
    // Cross-episode alias flexibility (e.g. ep 4 vs 5)
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

function resultToBlobUrl(result: any): string | null {
  if (!result) return null;
  try {
    if (result instanceof Blob) {
      return URL.createObjectURL(result);
    }
    if (result instanceof ArrayBuffer) {
      return URL.createObjectURL(new Blob([result], { type: 'video/mp4' }));
    }
    if (result && result.buffer instanceof ArrayBuffer) {
      return URL.createObjectURL(new Blob([result.buffer], { type: 'video/mp4' }));
    }
    if (typeof result === 'string') {
      if (result.startsWith('blob:') || result.startsWith('http') || result.startsWith('/')) {
        return result;
      }
    }
    return null;
  } catch (e) {
    console.warn('[mediaStore] Error converting store result to blob URL:', e);
    return null;
  }
}

export const mediaStore = {
  async saveMedia(keyOrKeys: string | string[], file: Blob | File): Promise<string> {
    const keys = Array.isArray(keyOrKeys) ? keyOrKeys : [keyOrKeys];
    const validKeys = keys.filter((k): k is string => Boolean(k && k.trim()));
    if (validKeys.length === 0) {
      return URL.createObjectURL(file);
    }

    let blobToStore: Blob = file;
    try {
      if (file instanceof File) {
        const buffer = await file.arrayBuffer();
        blobToStore = new Blob([buffer], { type: file.type || 'video/mp4' });
      }
    } catch {
      blobToStore = file;
    }

    const immediateUrl = URL.createObjectURL(blobToStore);
    validKeys.forEach((key) => activeBlobUrls.set(key, immediateUrl));

    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);

        validKeys.forEach((key) => {
          store.put(blobToStore, key);
        });

        tx.oncomplete = () => {
          resolve(immediateUrl);
        };

        tx.onerror = () => {
          resolve(immediateUrl);
        };
      });
    } catch (e) {
      console.warn('Failed to save media in IndexedDB, fallback to in-memory URL:', e);
      return immediateUrl;
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
            const url = resultToBlobUrl(req.result);
            if (url) {
              resolved = true;
              validKeys.forEach((k) => activeBlobUrls.set(k, url));
              resolve(url);
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
   * and if not found, scanning all IndexedDB keys for multi-tier fuzzy matching.
   */
  async findEpisodeMedia(params: EpisodeMediaParams): Promise<string | null> {
    const candidateKeys = generateEpisodeMediaKeys(params);
    console.log('[mediaStore] Searching media for candidate keys:', candidateKeys);
    
    const directMatch = await this.getMediaUrl(candidateKeys);
    if (directMatch) {
      console.log('[mediaStore] Direct candidate match found in cache/DB:', directMatch);
      return directMatch;
    }

    // Multi-tier fuzzy matching across all stored keys in IndexedDB
    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.getAllKeys();

        req.onsuccess = () => {
          const allKeys = (req.result || []).map((k) => String(k));
          console.log('[mediaStore] All stored keys in IndexedDB:', allKeys);
          if (allKeys.length === 0) {
            console.warn('[mediaStore] IndexedDB is currently empty (no video blobs saved).');
            resolve(null);
            return;
          }

          const epNum = params.episodeNumber !== undefined ? String(params.episodeNumber).trim() : null;
          const sId = params.seriesId ? params.seriesId.replace(/^story_/, '') : '';
          const titleTokens = params.title ? normalizeKey(params.title).split('_').filter(t => t.length > 2) : [];

          let bestKey: string | null = null;

          // Tier 1: Match series ID + episode number (e.g. queen_of_jozi + 5)
          if (sId && epNum) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (!lowerKey.startsWith('thumb_') && lowerKey.includes(sId) && (lowerKey.includes(`_${epNum}`) || lowerKey.includes(`ep${epNum}`))) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 2: Match by energy/pulse keywords if applicable
          if (!bestKey) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (!lowerKey.startsWith('thumb_') && (lowerKey.includes('energy') || lowerKey.includes('pulse') || lowerKey.includes('pusle'))) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 3: Match series ID with ANY video key (e.g. video_story_queen_of_jozi_*)
          if (!bestKey && sId) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (!lowerKey.startsWith('thumb_') && lowerKey.includes(sId) && (lowerKey.startsWith('video_') || lowerKey.startsWith('media_'))) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 4: Match title tokens
          if (!bestKey && titleTokens.length > 0) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (!lowerKey.startsWith('thumb_') && titleTokens.some(token => lowerKey.includes(token))) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 5: Match episode ID
          if (!bestKey && params.episodeId) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (!lowerKey.startsWith('thumb_') && lowerKey.includes(params.episodeId.toLowerCase())) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 6: For custom episodes (>=4), pick any video key in store
          if (!bestKey && epNum && Number(epNum) >= 4) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (lowerKey.startsWith('video_') || lowerKey.startsWith('media_')) {
                bestKey = key;
                break;
              }
            }
          }

          console.log('[mediaStore] Best fuzzy matched key:', bestKey);

          if (bestKey) {
            const getReq = store.get(bestKey);
            getReq.onsuccess = () => {
              const url = resultToBlobUrl(getReq.result);
              console.log('[mediaStore] Unpacked blob URL for', bestKey, '=>', url);
              if (url) {
                candidateKeys.forEach((k) => activeBlobUrls.set(k, url));
                activeBlobUrls.set(bestKey!, url);
                resolve(url);
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

  async getAllStoredKeys(): Promise<string[]> {
    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.getAllKeys();
        req.onsuccess = () => resolve((req.result || []).map(String));
        req.onerror = () => resolve([]);
      });
    } catch {
      return [];
    }
  },
};
