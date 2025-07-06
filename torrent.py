import bencodepy
import hashlib
import math
import os
from pprint import pprint

class Metadata:
    def __init__(self):
        self.torrent_file = {}
        self.total_length = 0
        self.piece_length = 0
        self.pieces = b''
        self.piece_hashes = []  # Initialize as empty list
        self.info_hash = ''
        self.peer_id = ''
        self.announce_list = []
        self.file_names = []
        self.number_of_pieces = 0

    def decode_torrent_file(self, path):
        with open(path, 'rb') as f:
            contents = f.read()
        
        self.torrent_file = bencodepy.decode(contents)
        self.torrent_file = self._decode_keys(self.torrent_file)
        
        info = self.torrent_file['info']
        
        # Size of each piece in bytes
        self.piece_length = info['piece length']
        
        # Get the concatenated SHA-1 hashes of each piece
        self.pieces = info['pieces']
        
        # Split pieces into individual 20-byte hashes
        self.piece_hashes = [
            self.pieces[i:i+20] for i in range(0, len(self.pieces), 20)
        ]
        
        # Encode info dictionary to calculate info_hash
        # Need to re-encode the original info dict (not decoded version)
        original_torrent = bencodepy.decode(contents)
        raw_info = bencodepy.encode(original_torrent[b'info'])
        
        # Compute the hash of raw info
        self.info_hash = hashlib.sha1(raw_info).hexdigest()
        
        self.announce_list = self.get_trackers()
        self.init_files()
        self.number_of_pieces = math.ceil(self.total_length / self.piece_length)
        
        ################# for now output is off
        #self.print_output()
        ####################

    def print_output(self):
        print("=== Torrent Metadata ===")
        print(f"Info Hash: {self.info_hash}")
        print(f"Piece Length: {self.piece_length}")
        print(f"Number of Pieces: {self.number_of_pieces}")
        print(f"Total Size: {self.total_length} bytes")
        print(f"Trackers: {self.announce_list}")
        print(f"Files: {self.file_names}")

    def _decode_keys(self, data):
        """Helper function to convert bytes keys to string recursively."""
        if isinstance(data, dict):
            return {k.decode() if isinstance(k, bytes) else k: self._decode_keys(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._decode_keys(i) for i in data]
        elif isinstance(data, bytes):
            try:
                return data.decode()
            except:
                return data
        else:
            return data

    def get_trackers(self):
        """
        Helper to find trackers, they are inside announce-list
        """
        trackers = []
        if 'announce-list' in self.torrent_file:
            # Multiple trackers at same level
            for level in self.torrent_file['announce-list']:
                for url in level:
                    trackers.append(url)
        # Single file case
        elif 'announce' in self.torrent_file:
            trackers.append(self.torrent_file['announce'])
        return trackers

    def init_files(self):
        """
        Handle multiple files in folder structure, else handle normally
        """
        info = self.torrent_file['info']
        if 'files' in info:
            # Multi-file torrent
            for file in info['files']:
                length = file['length']
                path = os.path.join(*file['path'])
                self.file_names.append(path)
                self.total_length += length
        else:
            # Single file torrent
            self.file_names.append(info['name'])
            self.total_length = info['length']

if __name__ == "__main__":
    meta = Metadata()
    meta.decode_torrent_file('test.torrent')