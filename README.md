# NetFlacks — Torrent Style Netflix Clone

## Overview

NetFlacks is a decentralized video streaming platform inspired by the BitTorrent protocol. It leverages peer-to-peer (P2P) networking to distribute video content efficiently, reducing reliance on centralized servers, improving bandwidth utilization, and enabling real-time streaming even in low-bandwidth or unstable network environments.

---

## Motivation & Problem Domain

- **Bandwidth Utilization & Server Load:** Centralized streaming services face high bandwidth costs and server congestion during peak hours.
- **Unstable Networks:** Traditional streaming struggles in low-bandwidth regions; P2P adapts dynamically to fluctuating connections.
- **Decentralized Storage:** Video content is distributed across peer devices, eliminating the need for costly centralized data centers.
- **Security:** Reduces single points of failure with distributed architecture.
- **Cost Efficiency:** Eliminates CDN expenses via peer-assisted delivery.

---

## Objectives & Features

### Core Objectives

- Build a fully decentralized P2P video distribution system inspired by BitTorrent.
- Implement Distributed Hash Table (DHT) for trackerless peer discovery.
- Adaptive chunking of videos into streamable pieces (256KB - 1MB).
- Real-time playback with chunk prioritization for seamless viewing.
- Lightweight, responsive web-based user interface.

### Key Features

- **Pure P2P Storage:**
  - No central storage; videos reside exclusively on peers.
  - Automatic replication of video chunks to maintain availability.
  - Temporary caching of watched segments on viewer devices.
  - Redistribution of chunks when peers disconnect.

- **Torrent-Style Streaming Engine:**
  - Video chunking with playback order prioritization.
  - Parallel chunk downloads from multiple peers.
  - Buffer-aware prefetching to ensure smooth playback.

- **Distributed Discovery System:**
  - DHT-based decentralized peer lookup.
  - NAT traversal via STUN/TURN servers.
  - Swarm health monitoring.

- **Hybrid CDN/P2P Delivery:**
  - Central server fallback for initial video chunks.
  - Automatic P2P scaling based on demand.
  - Bandwidth-saving mode for mobile users.

- **Encrypted Content Sharing** for privacy and security.

- **Adaptive Streaming Dashboard** for real-time monitoring.

---

## Tools & Technologies

- **Frontend:** Next.js, Tailwind CSS for a lightweight and responsive web UI.
- **Backend:** Python with FastAPI for scalable API and business logic.
- **Video Processing:** OpenCV and FFmpeg.wasm for video frame handling and encoding.
- **P2P Communication:** WebRTC for real-time peer-to-peer connections.
- **Torrent Protocol:** WebTorrent for BitTorrent functionality in browsers and Node.js.

---

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js and npm/yarn
- Modern browser supporting WebRTC

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/netflacks.git
   cd netflacks
