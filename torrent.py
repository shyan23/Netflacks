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
        #pprint(self.torrent_file)
        info = self.torrent_file['info']
        #size of each piece in bytes
        self.piece_length = info['piece length']
        #the concatenated SHA-1 hashes of each piece.
        self.pieces = info['pieces']
        
        '''
        abar encoded kora lage,cause .torrent file e kokhono ei encoded part rakhe na,
        and abar encode korei & hash kore amar info_hash ber kora lage
        '''
        
        raw_info = bencodepy.encode(info)
        # computes the hash of each raw info
        self.info_hash = hashlib.sha1(raw_info).hexdigest() # peer discover,DHT,handshake
        
        
        self.announce_list = self.get_trackers()

        self.init_files()

        self.number_of_pieces = math.ceil(self.total_length / self.piece_length)

        # print("=== Torrent Metadata ===")
        # print(f"Info Hash: {self.info_hash}")
        # print(f"Piece Length: {self.piece_length}")
        # print(f"Number of Pieces: {self.number_of_pieces}")
        # print(f"Total Size: {self.total_length} bytes")
        # print(f"Trackers: {self.announce_list}")
        # print(f"Files: {self.file_names}")

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
        '''
        Tracker khujte help kore, announce-list er bhitore ache
        '''
        trackers = []
        if 'announce-list' in self.torrent_file:
            # same level er bhitore onek gula trackers ache
            for level in self.torrent_file['announce-list']:
                for url in level:
                    trackers.append(url)
            # ekta file hole
        elif 'announce' in self.torrent_file:
            trackers.append(self.torrent_file['announce'])
        return trackers

    def init_files(self):
        '''
        multiple files thakle folder way te shajabo, else normally
        '''
        info = self.torrent_file['info']
        if 'files' in info:  
            for file in info['files']:
                length = file['length']
                path = os.path.join(*file['path'])
                self.file_names.append(path)
                self.total_length += length
        else:  
            self.file_names.append(info['name'])
            self.total_length = info['length']



if __name__ == "__main__":
    meta = Metadata()
    meta.decode_torrent_file('test.torrent')
