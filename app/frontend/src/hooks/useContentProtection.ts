import { useEffect, useState } from 'react';

interface ContentProtectionOptions {
  enabled?: boolean;
  watermarkText?: string;
  onCaptureAttempt?: () => void;
}

export const useContentProtection = ({
  enabled = true,
  watermarkText,
  onCaptureAttempt,
}: ContentProtectionOptions = {}) => {
  const [isSecurityAlertActive, setIsSecurityAlertActive] = useState<boolean>(false);
  const [securityMessage, setSecurityMessage] = useState<string>('');

  useEffect(() => {
    if (!enabled) return;

    const triggerSecurityNotice = (msg: string) => {
      setSecurityMessage(msg);
      setIsSecurityAlertActive(true);
      if (onCaptureAttempt) onCaptureAttempt();

      // Clear clipboard to prevent pasted screenshots
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText('');
        }
      } catch (_) {}

      setTimeout(() => {
        setIsSecurityAlertActive(false);
      }, 1200);
    };

    // 1. Block Context Menu (Right Click / Save Video As)
    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      triggerSecurityNotice('🔒 Content Protected: Saving video and right-click menus are disabled.');
      return false;
    };

    // 2. Block Dragging of Video & Media Elements
    const handleDragStart = (e: DragEvent) => {
      e.preventDefault();
      return false;
    };

    // 3. Intercept Screen Capture / DevTools / Save Keystrokes
    const handleKeyDown = (e: KeyboardEvent) => {
      // PrintScreen key
      if (e.key === 'PrintScreen' || e.code === 'PrintScreen') {
        e.preventDefault();
        triggerSecurityNotice('🔒 Screen Capture Blocked: Screenshotting copyrighted media is strictly prohibited.');
        return false;
      }

      // Ctrl+S / Cmd+S (Save Page / Save Media)
      if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
        e.preventDefault();
        triggerSecurityNotice('🔒 Saving content is disabled.');
        return false;
      }

      // Ctrl+U / Cmd+U (View Source)
      if ((e.ctrlKey || e.metaKey) && (e.key === 'u' || e.key === 'U')) {
        e.preventDefault();
        return false;
      }

      // F12 or Ctrl+Shift+I / Ctrl+Shift+J / Ctrl+Shift+C (DevTools Inspect)
      if (
        e.key === 'F12' ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && ['I', 'i', 'J', 'j', 'C', 'c'].includes(e.key))
      ) {
        e.preventDefault();
        triggerSecurityNotice('🔒 Developer tools inspection is locked for DRM protected media.');
        return false;
      }

      // Mac Screenshot shortcuts: Cmd+Shift+3, Cmd+Shift+4, Cmd+Shift+5
      if (e.metaKey && e.shiftKey && ['3', '4', '5'].includes(e.key)) {
        triggerSecurityNotice('🔒 Screen recording & capture are prohibited by Welele DRM.');
      }
    };

    // 4. Overwrite Screen Recording Web API if invoked
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia) {
        const originalGetDisplayMedia = navigator.mediaDevices.getDisplayMedia.bind(navigator.mediaDevices);
        navigator.mediaDevices.getDisplayMedia = async (...args) => {
          triggerSecurityNotice('🔒 Screen recording API is disabled for protected video playback.');
          throw new DOMException('Permission denied by DRM Policy', 'NotAllowedError');
        };
      }
    } catch (_) {}

    // Attach event listeners
    window.addEventListener('contextmenu', handleContextMenu, true);
    window.addEventListener('dragstart', handleDragStart, true);
    window.addEventListener('keydown', handleKeyDown, true);

    return () => {
      window.removeEventListener('contextmenu', handleContextMenu, true);
      window.removeEventListener('dragstart', handleDragStart, true);
      window.removeEventListener('keydown', handleKeyDown, true);
    };
  }, [enabled, onCaptureAttempt]);

  return {
    isSecurityAlertActive,
    securityMessage,
  };
};
