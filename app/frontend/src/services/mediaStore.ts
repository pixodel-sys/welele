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
  async saveMedia(key: string, file: Blob | File): Promise<string> {
    try {
      const db = await openDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        const req = store.put(file, key);
        req.onsuccess = () => {
          // Release previous object url if any
          if (activeBlobUrls.has(key)) {
            URL.revokeObjectURL(activeBlobUrls.get(key)!);
          }
          const url = URL.createObjectURL(file);
          activeBlobUrls.set(key, url);
          resolve(url);
        };
        req.onerror = () => reject(req.error);
      });
    } catch (e) {
      console.warn('Failed to save media in IndexedDB, fallback to in-memory URL:', e);
      const url = URL.createObjectURL(file);
      activeBlobUrls.set(key, url);
      return url;
    }
  },

  async getMediaUrl(key: string): Promise<string | null> {
    if (activeBlobUrls.has(key)) {
      return activeBlobUrls.get(key)!;
    }
    try {
      const db = await openDB();
      return new Promise((resolve) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.get(key);
        req.onsuccess = () => {
          if (req.result) {
            const url = URL.createObjectURL(req.result);
            activeBlobUrls.set(key, url);
            resolve(url);
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
