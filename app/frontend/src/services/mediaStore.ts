/**
 * Welele Media™ Persistent Local Media Storage
 * Uses IndexedDB to store and retrieve uploaded video & poster binaries,
 * ensuring custom uploaded assets persist across reloads, Creator, Admin, and Viewer surfaces.
 * Strictly scopes keys to series ID and episode number to prevent cross-contamination.
 */

const DB_NAME = 'welele_media_cache';
const DB_VERSION = 2; // Incremented for automatic cleanup of stale generic keys
const STORE_NAME = 'media_blobs';

const GENERIC_STALE_KEYS = new Set([
  '/videos/welele_placeholder.mp4',
  '/videos/welele_ident.mp4',
  'welele_placeholder.mp4',
  'welele_ident.mp4',
  'placeholder',
  'ident',
  'energy_pusle',
  'energy_pulse',
  'video_energy_pusle',
  'video_energy_pulse',
  'undefined',
  'video_undefined',
  'null',
  'video_null',
]);

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
    req.onsuccess = () => {
      const db = req.result;
      purgeStaleKeys(db);
      resolve(db);
    };
    req.onerror = () => reject(req.error);
  });
}

function purgeStaleKeys(db: IDBDatabase) {
  try {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.getAllKeys();
    req.onsuccess = () => {
      const keys = (req.result || []).map(String);
      keys.forEach((k) => {
        const lower = k.toLowerCase();
        if (
          GENERIC_STALE_KEYS.has(lower) ||
          lower.includes('placeholder') ||
          lower.includes('welele_ident') ||
          lower === 'video_energy_pusle' ||
          lower === 'energy_pusle'
        ) {
          store.delete(k);
          activeBlobUrls.delete(k);
          console.log('[mediaStore] Purged stale generic key from IndexedDB:', k);
        }
      });
    };
  } catch (e) {
    console.warn('[mediaStore] Could not run purgeStaleKeys:', e);
  }
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
  const { seriesId, seriesTitle, episodeNumber, episodeId, title } = params;

  const rawSId = seriesId
    ? seriesId.replace(/^story_/, '')
    : seriesTitle
    ? normalizeKey(seriesTitle)
    : null;
  const epNum =
    episodeNumber !== undefined && episodeNumber !== null
      ? String(episodeNumber).trim()
      : null;
  const titleSlug = title ? normalizeKey(title) : null;

  if (episodeId && episodeId !== 'undefined' && episodeId !== 'null') {
    keys.push(`video_${episodeId}`, `media_${episodeId}`, episodeId);
    if (rawSId) {
      keys.push(`video_${rawSId}_${episodeId}`);
    }
  }

  if (rawSId && epNum) {
    keys.push(`video_story_${rawSId}_${epNum}`);
    keys.push(`video_${rawSId}_${epNum}`);
    keys.push(`video_${rawSId}_ep_${epNum}`);
    keys.push(`video_${rawSId}_ep${epNum}`);
    keys.push(`video_${rawSId}_${epNum}_master`);
  }

  if (rawSId && titleSlug) {
    keys.push(`video_${rawSId}_${titleSlug}`);
    if (epNum) {
      keys.push(`video_${rawSId}_${titleSlug}_${epNum}`);
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
    const validKeys = keys.filter((k): k is string => Boolean(k && k.trim() && !GENERIC_STALE_KEYS.has(k.toLowerCase())));
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
    const validKeys = keys.filter((k): k is string => Boolean(k && k.trim() && !GENERIC_STALE_KEYS.has(k.toLowerCase())));
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
   * Intelligently resolves episode media strictly scoped to the series ID,
   * episode number, or episode ID.
   */
  async findEpisodeMedia(params: EpisodeMediaParams): Promise<string | null> {
    const candidateKeys = generateEpisodeMediaKeys(params);
    if (candidateKeys.length === 0) return null;

    const directMatch = await this.getMediaUrl(candidateKeys);
    if (directMatch) {
      return directMatch;
    }

    // Scoped matching across stored keys in IndexedDB
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

          let bestKey: string | null = null;

          // Tier 1: Match series ID + episode number (e.g. blood_ties_4, queen_of_jozi_5)
          if (sId && epNum) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (
                !lowerKey.startsWith('thumb_') &&
                !GENERIC_STALE_KEYS.has(lowerKey) &&
                lowerKey.includes(sId) &&
                (lowerKey.includes(`_${epNum}`) || lowerKey.includes(`ep_${epNum}`) || lowerKey.includes(`ep${epNum}`))
              ) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 2: Match series ID + exact episode title tokens
          if (!bestKey && sId && titleTokens.length > 0) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (
                !lowerKey.startsWith('thumb_') &&
                !GENERIC_STALE_KEYS.has(lowerKey) &&
                lowerKey.includes(sId) &&
                titleTokens.every(token => lowerKey.includes(token))
              ) {
                bestKey = key;
                break;
              }
            }
          }

          // Tier 3: Match exact episode ID
          if (!bestKey && params.episodeId) {
            for (const key of allKeys) {
              const lowerKey = key.toLowerCase();
              if (
                !lowerKey.startsWith('thumb_') &&
                !GENERIC_STALE_KEYS.has(lowerKey) &&
                lowerKey.includes(params.episodeId.toLowerCase())
              ) {
                bestKey = key;
                break;
              }
            }
          }

          if (bestKey) {
            const getReq = store.get(bestKey);
            getReq.onsuccess = () => {
              const url = resultToBlobUrl(getReq.result);
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

  async clearAllCache(): Promise<void> {
    activeBlobUrls.clear();
    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        const req = store.clear();
        req.onsuccess = () => resolve();
        req.onerror = () => resolve();
      });
    } catch {
      // ignore
    }
  }
};
