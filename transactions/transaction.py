import hashlib
import json
import time
from typing import List

class Transaction:
    def __init__(self, sender: str, receiver: str, amount: float):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = time.time()
        self.signatures: Dict[str, bytes] = {}

    @property
    def hash(self) -> str:
        data = json.dumps({
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "timestamp": self.timestamp
        }, sort_keys=True).encode()
        return hashlib.sha3_256(data).hexdigest()

    def add_signature(self, algorithm: str, signature: bytes):
        self.signatures[algorithm] = signature

class TransactionPool:
    def __init__(self):
        self.pool: List[Transaction] = []
        self.lock = threading.Lock()  # Добавлено для безопасности

    def add_transaction(self, tx: Transaction):
        with self.lock:
            self.pool.append(tx)

    def get_batch(self, size: int) -> List[Transaction]:
        with self.lock:
            batch = self.pool[:size]
            self.pool = self.pool[size:]
            return batch
