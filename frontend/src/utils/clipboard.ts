/**
 * Copy text to the clipboard.
 *
 * Uses the async Clipboard API in secure contexts (HTTPS / localhost) and falls
 * back to execCommand elsewhere, since SkillHub is often served over plain HTTP
 * on an internal network. Resolves to whether the copy succeeded.
 */
export const copyText = async (text: string): Promise<boolean> => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }

    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    textArea.style.top = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      return document.execCommand('copy');
    } finally {
      document.body.removeChild(textArea);
    }
  } catch (error) {
    console.error('Copy failed:', error);
    return false;
  }
};
