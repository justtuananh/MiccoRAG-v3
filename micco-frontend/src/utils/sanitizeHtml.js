import DOMPurify from 'dompurify';

// Untrusted document, approval and chat content share one narrow HTML policy.
const ALLOWED_TAGS = [
  'a', 'b', 'blockquote', 'br', 'button', 'code', 'dd', 'div', 'dl', 'dt',
  'em', 'h1', 'h2', 'h3', 'h4', 'hr', 'i', 'img', 'li', 'mark', 'ol', 'p',
  'pre', 'span', 'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'th',
  'thead', 'tr', 'u', 'ul',
];
const ALLOWED_ATTR = [
  'alt', 'class', 'data-image-doc-id', 'data-image-id', 'data-index',
  'data-source-id', 'href', 'id', 'src',
  'title', 'type',
];

export function sanitizeHtml(html) {
  return DOMPurify.sanitize(String(html ?? ''), {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
    FORBID_ATTR: ['style'],
  });
}

export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]);
}
