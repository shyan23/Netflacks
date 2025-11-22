import { useState, useEffect, useCallback } from 'react';
import { StreamStatus } from '@/types';
import { getStreamStatus } from '@/lib/api';

export function useStreamStatus(videoId: string | null, pollInterval = 500) {
  const [streamStatus, setStreamStatus] = useState<StreamStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const fetchStatus = useCallback(async () => {
    if (!videoId) return;
    const status = await getStreamStatus(videoId);
    setStreamStatus(status);
  }, [videoId]);

  const startPolling = useCallback(() => {
    setIsPolling(true);
  }, []);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
  }, []);

  useEffect(() => {
    if (!videoId || !isPolling) return;

    fetchStatus();
    const interval = setInterval(fetchStatus, pollInterval);

    return () => clearInterval(interval);
  }, [videoId, isPolling, pollInterval, fetchStatus]);

  return {
    streamStatus,
    isPolling,
    startPolling,
    stopPolling,
    refetch: fetchStatus,
  };
}
