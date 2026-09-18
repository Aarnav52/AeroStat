import { useState, useEffect, useCallback } from 'react';
import { fetchHealth } from '../api/apiService';

// Default polling interval: 30 seconds
const HEALTH_POLL_INTERVAL = 30000;

export default function useNetworkStatus() {
  const [isBrowserOnline, setIsBrowserOnline] = useState(navigator.onLine);
  const [isBackendReachable, setIsBackendReachable] = useState(true);
  const [lastChecked, setLastChecked] = useState(new Date());

  const checkBackendHealth = useCallback(async () => {
    if (!navigator.onLine) {
      setIsBackendReachable(false);
      return;
    }
    try {
      await fetchHealth();
      setIsBackendReachable(true);
    } catch (error) {
      setIsBackendReachable(false);
    }
    setLastChecked(new Date());
  }, []);

  useEffect(() => {
    // Standard browser online/offline events
    const handleOnline = () => {
      setIsBrowserOnline(true);
      checkBackendHealth(); // Immediate check on recovery
    };
    const handleOffline = () => {
      setIsBrowserOnline(false);
      setIsBackendReachable(false); // If browser offline, backend is unreachable
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial check
    checkBackendHealth();

    // Periodic backend polling
    const intervalId = setInterval(checkBackendHealth, HEALTH_POLL_INTERVAL);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(intervalId);
    };
  }, [checkBackendHealth]);

  // Derived state helper
  const status = isBrowserOnline && isBackendReachable ? 'ONLINE' : 'OFFLINE';

  return {
    isBrowserOnline,
    isBackendReachable,
    status,
    lastChecked,
    checkBackendHealth
  };
}
