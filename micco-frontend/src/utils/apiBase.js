export function resolveApiBase() {
  const configuredBase = import.meta.env.VITE_API_BASE_URL || '';
  if (!configuredBase || typeof window === 'undefined') {
    return configuredBase;
  }

  const forceSameOrigin = import.meta.env.VITE_FORCE_SAME_ORIGIN_API === 'true';

  try {
    const currentOrigin = window.location.origin;
    const configuredOrigin = new URL(configuredBase, currentOrigin).origin;
    const currentHost = window.location.hostname;
    const tunnelInvolved =
      currentHost.endsWith('trycloudflare.com') || configuredOrigin.includes('trycloudflare.com');

    if ((forceSameOrigin || tunnelInvolved) && configuredOrigin !== currentOrigin) {
      return '';
    }
  } catch (error) {
    console.warn('Invalid VITE_API_BASE_URL, using configured value as-is:', configuredBase, error);
    return configuredBase;
  }

  return configuredBase;
}
