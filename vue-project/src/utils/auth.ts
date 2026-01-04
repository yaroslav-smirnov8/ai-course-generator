/**
 * Authentication utilities for the application
 */

/**
 * Get authentication headers for API requests
 * @returns Object with authentication headers
 */
export const getAuthHeaders = (): Record<string, string> => {
  // Get authentication data from Telegram WebApp
  const webApp = window.Telegram?.WebApp;
  const webAppData = webApp?.initData;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };

  if (webAppData) {
    headers['Authorization'] = `tma ${webAppData}`;
  }

  return headers;
};
