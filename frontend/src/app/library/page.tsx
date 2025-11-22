'use client';

import { useState, useEffect, useCallback } from 'react';
import { Video, StreamStatus } from '@/types';
import { getVideos, getStreamStatus } from '@/lib/api';
import VideoCard from '@/components/VideoCard';
import { RefreshIcon, FilmIcon } from '@/components/Icons';

export default function LibraryPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [streamStatuses, setStreamStatuses] = useState<Record<string, StreamStatus | null>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchVideos = useCallback(async () => {
    const data = await getVideos();
    setVideos(data);
    setLoading(false);
  }, []);

  const fetchStreamStatuses = useCallback(async () => {
    const statuses: Record<string, StreamStatus | null> = {};
    await Promise.all(
      videos.map(async (video) => {
        const status = await getStreamStatus(video.video_id);
        statuses[video.video_id] = status;
      })
    );
    setStreamStatuses(statuses);
  }, [videos]);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  useEffect(() => {
    if (videos.length > 0) {
      fetchStreamStatuses();
      const interval = setInterval(fetchStreamStatuses, 2000);
      return () => clearInterval(interval);
    }
  }, [videos, fetchStreamStatuses]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchVideos();
    setRefreshing(false);
  };

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">My Library</h1>
          <p className="text-gray-400 mt-1">
            {videos.length} {videos.length === 1 ? 'video' : 'videos'} available
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors disabled:opacity-50"
        >
          <RefreshIcon className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="space-y-3">
              <div className="aspect-video skeleton rounded-lg" />
              <div className="h-4 skeleton rounded w-3/4" />
              <div className="h-3 skeleton rounded w-1/2" />
            </div>
          ))}
        </div>
      )}

      {/* Videos Grid */}
      {!loading && videos.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {videos.map((video) => (
            <VideoCard
              key={video.video_id}
              video={video}
              streamStatus={streamStatuses[video.video_id]}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && videos.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <FilmIcon className="w-24 h-24 text-gray-600 mb-6" />
          <h2 className="text-2xl font-bold mb-2">No Videos Found</h2>
          <p className="text-gray-400 mb-6 text-center max-w-md">
            Your library is empty. Upload a video to get started with P2P streaming.
          </p>
          <a
            href="/upload"
            className="px-6 py-3 bg-[#e50914] text-white font-semibold rounded hover:bg-[#f40612] transition-colors"
          >
            Upload Video
          </a>
        </div>
      )}
    </div>
  );
}
