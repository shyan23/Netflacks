import { Video, StreamStatus, UploadResponse } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export async function getVideos(): Promise<Video[]> {
  try {
    const response = await fetch(`${API_BASE}/api/videos`, {
      cache: 'no-store',
    });
    if (!response.ok) {
      throw new Error('Failed to fetch videos');
    }
    return response.json();
  } catch (error) {
    console.error('Error fetching videos:', error);
    return [];
  }
}

export async function getStreamStatus(videoId: string): Promise<StreamStatus | null> {
  try {
    const response = await fetch(`${API_BASE}/api/stream-status/${videoId}`, {
      cache: 'no-store',
    });
    if (!response.ok) {
      return null;
    }
    return response.json();
  } catch (error) {
    console.error('Error fetching stream status:', error);
    return null;
  }
}

export async function initializeStream(videoId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/stream/${videoId}`, {
      method: 'HEAD',
    });
    return response.ok || response.status === 206;
  } catch (error) {
    console.error('Error initializing stream:', error);
    return false;
  }
}

export async function uploadVideo(file: File): Promise<UploadResponse | null> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload video');
    }

    return response.json();
  } catch (error) {
    console.error('Error uploading video:', error);
    return null;
  }
}

export function getStreamUrl(videoId: string): string {
  return `${API_BASE}/stream/${videoId}`;
}

export async function checkServerHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/api/videos`, {
      method: 'GET',
      cache: 'no-store',
    });
    return response.ok;
  } catch {
    return false;
  }
}
