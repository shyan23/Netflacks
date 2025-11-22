'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Video, StreamStatus } from '@/types';
import { PlayIcon, FilmIcon } from './Icons';

interface VideoCardProps {
  video: Video;
  streamStatus?: StreamStatus | null;
}

export default function VideoCard({ video, streamStatus }: VideoCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  const isStreaming = streamStatus && streamStatus.progress > 0;
  const isReady = streamStatus?.ready;
  const progress = streamStatus?.progress || 0;

  return (
    <Link href={`/watch/${video.video_id}`}>
      <div
        className="group relative rounded-lg overflow-hidden cursor-pointer transform transition-all duration-300 hover:scale-105 hover:z-10"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Thumbnail placeholder */}
        <div className="relative aspect-video bg-gradient-to-br from-gray-800 to-gray-900">
          <div className="absolute inset-0 flex items-center justify-center">
            <FilmIcon className="w-16 h-16 text-gray-600" />
          </div>

          {/* Overlay on hover */}
          <div
            className={`absolute inset-0 bg-black/40 transition-opacity duration-300 ${
              isHovered ? 'opacity-100' : 'opacity-0'
            }`}
          />

          {/* Play button */}
          <div
            className={`absolute inset-0 flex items-center justify-center transition-all duration-300 ${
              isHovered ? 'opacity-100 scale-100' : 'opacity-0 scale-75'
            }`}
          >
            <div className="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center shadow-lg">
              <PlayIcon className="w-6 h-6 text-black ml-1" />
            </div>
          </div>

          {/* Status badge */}
          {isStreaming && (
            <div className="absolute top-2 right-2">
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${
                  isReady
                    ? 'bg-green-500/90 text-white'
                    : 'bg-yellow-500/90 text-black'
                }`}
              >
                {isReady ? 'Ready' : 'Buffering'}
              </span>
            </div>
          )}

          {/* Progress bar */}
          {isStreaming && !isReady && (
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-700">
              <div
                className="h-full bg-[#e50914] transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
        </div>

        {/* Info section */}
        <div className="p-3 bg-[#1a1a1a] group-hover:bg-[#2a2a2a] transition-colors">
          <h3 className="text-sm font-medium text-white truncate">
            {video.filename.replace(/\.[^/.]+$/, '')}
          </h3>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xs text-gray-400">
              {video.chunks} chunks
            </span>
            {isStreaming && (
              <span className="text-xs text-gray-400">
                {progress.toFixed(0)}%
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
