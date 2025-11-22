'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Video, StreamStatus } from '@/types';
import { getVideos, getStreamStatus, initializeStream, getStreamUrl } from '@/lib/api';
import VideoPlayer from '@/components/VideoPlayer';
import { BackIcon, NetworkIcon, LoadingIcon } from '@/components/Icons';

export default function WatchPage() {
  const params = useParams();
  const router = useRouter();
  const videoId = params.videoId as string;

  const [video, setVideo] = useState<Video | null>(null);
  const [streamStatus, setStreamStatus] = useState<StreamStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [initializing, setInitializing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch video details
  useEffect(() => {
    const fetchVideo = async () => {
      const videos = await getVideos();
      const found = videos.find((v) => v.video_id === videoId);
      if (found) {
        setVideo(found);
      } else {
        setError('Video not found');
      }
      setLoading(false);
    };
    fetchVideo();
  }, [videoId]);

  // Initialize stream
  useEffect(() => {
    const initStream = async () => {
      if (!video) return;
      setInitializing(true);
      const success = await initializeStream(videoId);
      if (!success) {
        setError('Failed to initialize stream');
      }
      setInitializing(false);
    };
    initStream();
  }, [video, videoId]);

  // Poll stream status
  const pollStreamStatus = useCallback(async () => {
    if (!video) return;
    const status = await getStreamStatus(videoId);
    setStreamStatus(status);
  }, [video, videoId]);

  useEffect(() => {
    if (!video || error) return;

    // Initial fetch
    pollStreamStatus();

    // Poll every 500ms
    const interval = setInterval(pollStreamStatus, 500);
    return () => clearInterval(interval);
  }, [video, error, pollStreamStatus]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingIcon className="w-12 h-12 text-[#e50914]" />
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <h1 className="text-2xl font-bold mb-4">{error || 'Video not found'}</h1>
        <Link
          href="/library"
          className="px-6 py-3 bg-[#e50914] text-white font-semibold rounded hover:bg-[#f40612] transition-colors"
        >
          Back to Library
        </Link>
      </div>
    );
  }

  const videoTitle = video.filename.replace(/\.[^/.]+$/, '');

  return (
    <div className="min-h-screen bg-black">
      {/* Back button */}
      <div className="absolute top-20 left-4 z-50">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 px-4 py-2 bg-black/50 hover:bg-black/80 rounded-full transition-colors"
        >
          <BackIcon className="w-5 h-5" />
          <span>Back</span>
        </button>
      </div>

      {/* Video Player Section */}
      <div className="w-full max-w-7xl mx-auto px-4 pt-20 pb-8">
        <VideoPlayer
          videoId={videoId}
          streamUrl={getStreamUrl(videoId)}
          title={videoTitle}
          streamStatus={streamStatus}
        />

        {/* Video Info */}
        <div className="mt-8 space-y-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">{videoTitle}</h1>
            <div className="flex items-center gap-4 text-gray-400">
              <span>{video.chunks} chunks</span>
              <span>•</span>
              <span className="font-mono text-sm">ID: {videoId.substring(0, 12)}...</span>
            </div>
          </div>

          {/* Stream Info Panel */}
          <div className="p-6 bg-white/5 rounded-xl border border-white/10">
            <div className="flex items-center gap-3 mb-4">
              <NetworkIcon className="w-6 h-6 text-[#e50914]" />
              <h2 className="text-lg font-semibold">P2P Stream Status</h2>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-white/5 rounded-lg">
                <p className="text-gray-400 text-sm mb-1">Status</p>
                <p className={`font-semibold ${streamStatus?.ready ? 'text-green-500' : 'text-yellow-500'}`}>
                  {initializing ? 'Initializing...' : streamStatus?.ready ? 'Ready' : 'Buffering'}
                </p>
              </div>
              <div className="p-4 bg-white/5 rounded-lg">
                <p className="text-gray-400 text-sm mb-1">Progress</p>
                <p className="font-semibold">{streamStatus?.progress?.toFixed(1) || 0}%</p>
              </div>
              <div className="p-4 bg-white/5 rounded-lg">
                <p className="text-gray-400 text-sm mb-1">Chunks</p>
                <p className="font-semibold">
                  {streamStatus?.downloaded || 0} / {streamStatus?.total || video.chunks}
                </p>
              </div>
              <div className="p-4 bg-white/5 rounded-lg">
                <p className="text-gray-400 text-sm mb-1">Downloaded</p>
                <p className="font-semibold">
                  {streamStatus?.current_size
                    ? `${(streamStatus.current_size / (1024 * 1024)).toFixed(1)} MB`
                    : '0 MB'}
                </p>
              </div>
            </div>

            {/* Progress Bar */}
            {streamStatus && !streamStatus.ready && (
              <div className="mt-4">
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#e50914] transition-all duration-300"
                    style={{ width: `${streamStatus.progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
