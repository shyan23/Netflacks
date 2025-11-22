'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Video } from '@/types';
import { getVideos } from '@/lib/api';
import VideoCard from '@/components/VideoCard';
import { PlayIcon, UploadIcon, NetworkIcon, FilmIcon } from '@/components/Icons';

export default function Home() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [featuredVideo, setFeaturedVideo] = useState<Video | null>(null);

  useEffect(() => {
    const fetchVideos = async () => {
      const data = await getVideos();
      setVideos(data);
      if (data.length > 0) {
        setFeaturedVideo(data[0]);
      }
      setLoading(false);
    };
    fetchVideos();
  }, []);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative h-[80vh] flex items-center">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 to-transparent z-10" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#141414] via-transparent to-transparent z-10" />

        {/* Background pattern */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-[#e50914]/20 via-transparent to-transparent" />
        </div>

        {/* Content */}
        <div className="relative z-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="max-w-2xl">
            <h1 className="text-5xl md:text-7xl font-bold mb-4 tracking-tight">
              <span className="text-[#e50914]">Net</span>Flacks
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-6">
              Peer-to-Peer Video Streaming
            </p>
            <p className="text-gray-400 mb-8 text-lg leading-relaxed">
              Experience the future of video streaming. Your videos are distributed across
              a network of peers, enabling fast, resilient streaming with progressive playback.
            </p>

            <div className="flex flex-wrap gap-4">
              {featuredVideo ? (
                <Link
                  href={`/watch/${featuredVideo.video_id}`}
                  className="flex items-center gap-2 px-8 py-3 bg-white text-black font-semibold rounded hover:bg-gray-200 transition-colors"
                >
                  <PlayIcon className="w-6 h-6" />
                  Watch Now
                </Link>
              ) : (
                <Link
                  href="/library"
                  className="flex items-center gap-2 px-8 py-3 bg-white text-black font-semibold rounded hover:bg-gray-200 transition-colors"
                >
                  <FilmIcon className="w-6 h-6" />
                  Browse Library
                </Link>
              )}
              <Link
                href="/upload"
                className="flex items-center gap-2 px-8 py-3 bg-gray-600/80 text-white font-semibold rounded hover:bg-gray-600 transition-colors"
              >
                <UploadIcon className="w-5 h-5" />
                Upload Video
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="p-6 bg-white/5 rounded-lg border border-white/10 hover:border-[#e50914]/50 transition-colors">
            <NetworkIcon className="w-10 h-10 text-[#e50914] mb-4" />
            <h3 className="text-xl font-semibold mb-2">P2P Distribution</h3>
            <p className="text-gray-400">
              Videos are chunked and distributed across multiple peers for resilient streaming.
            </p>
          </div>
          <div className="p-6 bg-white/5 rounded-lg border border-white/10 hover:border-[#e50914]/50 transition-colors">
            <PlayIcon className="w-10 h-10 text-[#e50914] mb-4" />
            <h3 className="text-xl font-semibold mb-2">Progressive Streaming</h3>
            <p className="text-gray-400">
              Start watching immediately while chunks continue downloading in the background.
            </p>
          </div>
          <div className="p-6 bg-white/5 rounded-lg border border-white/10 hover:border-[#e50914]/50 transition-colors">
            <UploadIcon className="w-10 h-10 text-[#e50914] mb-4" />
            <h3 className="text-xl font-semibold mb-2">Easy Upload</h3>
            <p className="text-gray-400">
              Drag and drop your videos. They&apos;re automatically processed and distributed.
            </p>
          </div>
        </div>
      </section>

      {/* Recent Videos Section */}
      {videos.length > 0 && (
        <section className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Recently Added</h2>
            <Link
              href="/library"
              className="text-gray-400 hover:text-white transition-colors"
            >
              View All →
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="aspect-video skeleton rounded-lg" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {videos.slice(0, 5).map((video) => (
                <VideoCard key={video.video_id} video={video} />
              ))}
            </div>
          )}
        </section>
      )}

      {/* Empty State */}
      {!loading && videos.length === 0 && (
        <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center">
          <div className="max-w-md mx-auto">
            <FilmIcon className="w-20 h-20 text-gray-600 mx-auto mb-6" />
            <h2 className="text-2xl font-bold mb-2">No Videos Yet</h2>
            <p className="text-gray-400 mb-6">
              Be the first to upload a video to the P2P network.
            </p>
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#e50914] text-white font-semibold rounded hover:bg-[#f40612] transition-colors"
            >
              <UploadIcon className="w-5 h-5" />
              Upload Your First Video
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
