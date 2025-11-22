'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { uploadVideo } from '@/lib/api';
import { UploadIcon, CheckIcon, XIcon, LoadingIcon, FilmIcon } from '@/components/Icons';

type UploadState = 'idle' | 'uploading' | 'processing' | 'distributing' | 'success' | 'error';

interface UploadStep {
  label: string;
  status: 'pending' | 'active' | 'complete' | 'error';
}

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ video_id: string; filename: string } | null>(null);

  const steps: UploadStep[] = [
    { label: 'Uploading file', status: uploadState === 'uploading' ? 'active' : uploadState === 'idle' ? 'pending' : 'complete' },
    { label: 'Processing chunks', status: uploadState === 'processing' ? 'active' : ['idle', 'uploading'].includes(uploadState) ? 'pending' : 'complete' },
    { label: 'Distributing to peers', status: uploadState === 'distributing' ? 'active' : ['idle', 'uploading', 'processing'].includes(uploadState) ? 'pending' : 'complete' },
    { label: 'Complete', status: uploadState === 'success' ? 'complete' : uploadState === 'error' ? 'error' : 'pending' },
  ];

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && isValidVideoFile(droppedFile)) {
      setFile(droppedFile);
      setError(null);
    } else {
      setError('Please upload a valid video file (MP4, AVI, MOV, MKV, WebM)');
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && isValidVideoFile(selectedFile)) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please upload a valid video file (MP4, AVI, MOV, MKV, WebM)');
    }
  }, []);

  const isValidVideoFile = (file: File): boolean => {
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/webm'];
    const validExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    return validTypes.includes(file.type) || validExtensions.includes(extension);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleUpload = async () => {
    if (!file) return;

    setError(null);
    setUploadState('uploading');
    setProgress(25);

    try {
      // Simulate upload progress
      await new Promise(resolve => setTimeout(resolve, 500));
      setUploadState('processing');
      setProgress(50);

      await new Promise(resolve => setTimeout(resolve, 500));
      setUploadState('distributing');
      setProgress(75);

      const response = await uploadVideo(file);

      if (response) {
        setProgress(100);
        setUploadState('success');
        setResult(response);
      } else {
        throw new Error('Upload failed');
      }
    } catch (err) {
      setUploadState('error');
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadState('idle');
    setProgress(0);
    setError(null);
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold mb-2">Upload Video</h1>
        <p className="text-gray-400">
          Upload your video to distribute it across the P2P network
        </p>
      </div>

      {/* Upload Area */}
      <div className="bg-white/5 rounded-xl p-8 border border-white/10">
        {uploadState === 'idle' && !file && (
          <div
            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${
              dragActive
                ? 'border-[#e50914] bg-[#e50914]/10'
                : 'border-gray-600 hover:border-gray-500 hover:bg-white/5'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            <UploadIcon className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            <p className="text-xl font-medium mb-2">
              Drag and drop your video here
            </p>
            <p className="text-gray-400 mb-4">
              or click to browse
            </p>
            <p className="text-sm text-gray-500">
              Supported formats: MP4, AVI, MOV, MKV, WebM
            </p>
          </div>
        )}

        {/* File Selected */}
        {file && uploadState === 'idle' && (
          <div className="space-y-6">
            <div className="flex items-center gap-4 p-4 bg-white/5 rounded-lg">
              <div className="w-16 h-16 bg-gray-700 rounded-lg flex items-center justify-center">
                <FilmIcon className="w-8 h-8 text-gray-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{file.name}</p>
                <p className="text-sm text-gray-400">{formatFileSize(file.size)}</p>
              </div>
              <button
                onClick={handleReset}
                className="p-2 hover:bg-white/10 rounded-full transition-colors"
              >
                <XIcon className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <div className="flex gap-4">
              <button
                onClick={handleUpload}
                className="flex-1 py-3 bg-[#e50914] text-white font-semibold rounded-lg hover:bg-[#f40612] transition-colors"
              >
                Upload to Network
              </button>
              <button
                onClick={handleReset}
                className="px-6 py-3 bg-white/10 text-white font-semibold rounded-lg hover:bg-white/20 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Upload Progress */}
        {['uploading', 'processing', 'distributing'].includes(uploadState) && (
          <div className="space-y-8">
            <div className="text-center">
              <LoadingIcon className="w-16 h-16 text-[#e50914] mx-auto mb-4" />
              <p className="text-xl font-medium">
                {uploadState === 'uploading' && 'Uploading...'}
                {uploadState === 'processing' && 'Processing video chunks...'}
                {uploadState === 'distributing' && 'Distributing to P2P network...'}
              </p>
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#e50914] transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-center text-gray-400">{progress}%</p>
            </div>

            {/* Steps */}
            <div className="space-y-3">
              {steps.map((step, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      step.status === 'complete'
                        ? 'bg-green-500'
                        : step.status === 'active'
                        ? 'bg-[#e50914]'
                        : 'bg-gray-700'
                    }`}
                  >
                    {step.status === 'complete' && <CheckIcon className="w-4 h-4 text-white" />}
                    {step.status === 'active' && <LoadingIcon className="w-4 h-4 text-white" />}
                    {step.status === 'pending' && <span className="text-xs text-gray-400">{index + 1}</span>}
                  </div>
                  <span
                    className={
                      step.status === 'active'
                        ? 'text-white'
                        : step.status === 'complete'
                        ? 'text-green-500'
                        : 'text-gray-500'
                    }
                  >
                    {step.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Success State */}
        {uploadState === 'success' && result && (
          <div className="text-center space-y-6">
            <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto">
              <CheckIcon className="w-10 h-10 text-white" />
            </div>
            <div>
              <p className="text-xl font-medium mb-2">Upload Successful!</p>
              <p className="text-gray-400">
                Your video has been distributed across the P2P network
              </p>
            </div>

            <div className="p-4 bg-white/5 rounded-lg text-left">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Filename:</span>
                  <span>{result.filename}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Video ID:</span>
                  <span className="font-mono text-sm">{result.video_id.substring(0, 16)}...</span>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => router.push(`/watch/${result.video_id}`)}
                className="flex-1 py-3 bg-[#e50914] text-white font-semibold rounded-lg hover:bg-[#f40612] transition-colors"
              >
                Watch Now
              </button>
              <button
                onClick={handleReset}
                className="flex-1 py-3 bg-white/10 text-white font-semibold rounded-lg hover:bg-white/20 transition-colors"
              >
                Upload Another
              </button>
            </div>
          </div>
        )}

        {/* Error State */}
        {uploadState === 'error' && (
          <div className="text-center space-y-6">
            <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center mx-auto">
              <XIcon className="w-10 h-10 text-white" />
            </div>
            <div>
              <p className="text-xl font-medium mb-2">Upload Failed</p>
              <p className="text-gray-400">{error || 'An error occurred during upload'}</p>
            </div>
            <button
              onClick={handleReset}
              className="px-8 py-3 bg-[#e50914] text-white font-semibold rounded-lg hover:bg-[#f40612] transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && uploadState === 'idle' && (
          <div className="mt-4 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-center">
            {error}
          </div>
        )}
      </div>

      {/* Info Section */}
      <div className="mt-12 grid md:grid-cols-3 gap-6">
        <div className="p-6 bg-white/5 rounded-lg">
          <h3 className="font-semibold mb-2">1. Upload</h3>
          <p className="text-gray-400 text-sm">
            Select or drag your video file. We support most common formats.
          </p>
        </div>
        <div className="p-6 bg-white/5 rounded-lg">
          <h3 className="font-semibold mb-2">2. Process</h3>
          <p className="text-gray-400 text-sm">
            Your video is split into 1MB chunks and optimized for streaming.
          </p>
        </div>
        <div className="p-6 bg-white/5 rounded-lg">
          <h3 className="font-semibold mb-2">3. Distribute</h3>
          <p className="text-gray-400 text-sm">
            Chunks are replicated across peers for fast, resilient playback.
          </p>
        </div>
      </div>
    </div>
  );
}
