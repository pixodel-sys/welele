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
};
