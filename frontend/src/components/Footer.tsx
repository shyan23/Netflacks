import Link from 'next/link';
import { NetworkIcon } from './Icons';

export default function Footer() {
  return (
    <footer className="bg-black/50 border-t border-white/10 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <span className="text-[#e50914] text-2xl font-bold tracking-wider">
                NETFLACKS
              </span>
            </Link>
            <p className="text-gray-400 text-sm max-w-md">
              A peer-to-peer video streaming platform demonstrating progressive streaming
              with distributed content delivery across a network of peers.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/" className="text-gray-400 hover:text-white text-sm transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/library" className="text-gray-400 hover:text-white text-sm transition-colors">
                  Library
                </Link>
              </li>
              <li>
                <Link href="/upload" className="text-gray-400 hover:text-white text-sm transition-colors">
                  Upload
                </Link>
              </li>
            </ul>
          </div>

          {/* Tech Stack */}
          <div>
            <h3 className="text-white font-semibold mb-4">Technology</h3>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li className="flex items-center gap-2">
                <NetworkIcon className="w-4 h-4" />
                P2P Network
              </li>
              <li>DHT-based Discovery</li>
              <li>Progressive Streaming</li>
              <li>FFmpeg Processing</li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-white/10 text-center text-gray-500 text-sm">
          <p>Built with Next.js, FastAPI, and love for distributed systems</p>
        </div>
      </div>
    </footer>
  );
}
