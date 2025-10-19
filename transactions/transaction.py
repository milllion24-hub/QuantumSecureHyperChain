import hashlib
import json
import time
from typing import List, Dict
import threading

class Transaction:
    def __init__(self, sender: str, receiver: str, amount: float, tx_type: str = "transfer"):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.tx_type = tx_type
        self.timestamp = time.time()
        self.signatures: Dict[str, bytes] = {}
        self.fee = 0.001  # Базовая комиссия

    @property
    def hash(self) -> str:
        data = json.dumps({
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "tx_type": self.tx_type,
            "timestamp": self.timestamp,
            "fee": self.fee
        }, sort_keys=True).encode()
        return hashlib.sha3_256(data).hexdigest()

    def add_signature(self, algorithm: str, signature: bytes):
        self.signatures[algorithm] = signature

    def to_dict(self) -> Dict:
        return {
            "hash": self.hash,
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "tx_type": self.tx_type,
            "timestamp": self.timestamp,
            "fee": self.fee
        }

class TransactionPool:
    def __init__(self):
        self.pool: List[Transaction] = []
        self.lock = threading.Lock()

    def add_transaction(self, tx: Transaction):
        with self.lock:
            self.pool.append(tx)

    def get_batch(self, size: int) -> List[Transaction]:
        with self.lock:
            batch = self.pool[:size]
            self.pool = self.pool[size:]
            return batch

    def get_pool_size(self) -> int:
        with self.lock:
            return len(self.pool)

    def clear_pool(self):
        with self.lock:
            self.pool.clear()
