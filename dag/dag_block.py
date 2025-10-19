import hashlib
import json
import time
from typing import List, Dict

class DAGBlock:
    def __init__(self, shard_id: int, transactions: List, miner: str, previous_hashes: List[str]):
        self.shard_id = shard_id
        self.transactions = transactions
        self.miner = miner
        self.previous_hashes = previous_hashes
        self.timestamp = time.time()
        self.signatures: Dict[str, bytes] = {}
        self.merkle_root = self._calculate_merkle_root()
        self.hash = self._calculate_hash()
        self.nonce = 0  # Для PoW варианта, если понадобится

    def _calculate_merkle_root(self) -> str:
        if not self.transactions:
            return "0" * 64
        
        tx_hashes = [tx.hash for tx in self.transactions]
        
        # Простой Merkle tree calculation
        while len(tx_hashes) > 1:
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                if i + 1 < len(tx_hashes):
                    combined = tx_hashes[i] + tx_hashes[i + 1]
                else:
                    combined = tx_hashes[i] + tx_hashes[i]
                
                new_hash = hashlib.sha3_256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            tx_hashes = new_hashes
        
        return tx_hashes[0] if tx_hashes else "0" * 64

    def _calculate_hash(self) -> str:
        data = {
            "shard_id": self.shard_id,
            "merkle_root": self.merkle_root,
            "timestamp": self.timestamp,
            "previous_hashes": self.previous_hashes,
            "miner": self.miner,
            "nonce": self.nonce
        }
        return hashlib.sha3_256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def add_signature(self, algorithm: str, signature: bytes):
        self.signatures[algorithm] = signature

    def to_dict(self) -> Dict:
        return {
            "hash": self.hash,
            "shard_id": self.shard_id,
            "miner": self.miner,
            "timestamp": self.timestamp,
            "transaction_count": len(self.transactions),
            "previous_hashes": self.previous_hashes,
            "merkle_root": self.merkle_root
        }
