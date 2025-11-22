export interface Video {
  video_id: string;
  filename: string;
  chunks: number;
}

export interface StreamStatus {
  ready: boolean;
  progress: number;
  downloaded: number;
  total: number;
  file_size: number;
  current_size: number;
}

export interface UploadResponse {
  status: string;
  video_id: string;
  filename: string;
}

export interface SystemStatus {
  streaming_server: boolean;
  dht_node: boolean;
  peer_node: boolean;
}
