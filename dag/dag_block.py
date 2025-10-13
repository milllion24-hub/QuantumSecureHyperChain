from typing import List

class DAGBlock:
    def __init__(self, shard_id: int, transactions: List[Transaction], 
                 miner: str, previous_hashes: List[str]):
        self.shard_id = shard_id
        self.transactions = transactions
        self.miner = miner
        self.previous_hashes = previous_hashes
        self.timestamp = time.time()
        self.signatures: Dict[str, bytes] = {}
        self.merkle_root = self._calculate_merkle_root()
        self.hash = self._calculate_hash()

    def _calculate_merkle_root(self) -> str:
        # Реализация расчета Merkle-корня
        tx_hashes = [bytes.fromhex(tx.hash) for tx in self.transactions]
        combined = b"".join(tx_hashes)
        return hashlib.sha3_256(combined).hexdigest()

    def _calculate_hash(self) -> str:
        data = {
            "shard_id": self.shard_id,
            "merkle_root": self.merkle_root,
            "timestamp": self.timestamp,
            "previous_hashes": self.previous_hashes,
            "miner": self.miner
        }
        return hashlib.sha3_256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def add_signature(self, algorithm: str, signature: bytes):
        self.signatures[algorithm] = signature
