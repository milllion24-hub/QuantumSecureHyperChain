import threading
from typing import List, Set
from .dag_block import DAGBlock

class DAGShard:
    def __init__(self, shard_id: int):
        self.shard_id = shard_id
        self.blocks: List[DAGBlock] = []
        self.tips: Set[str] = set()  # Хэши последних блоков
        self.lock = threading.Lock()
        
    def add_block(self, block: DAGBlock) -> bool:
        """Добавляет блок в DAG шард"""
        with self.lock:
            # Проверяем, что блок ссылается на существующие tips
            if not all(prev_hash in [b.hash for b in self.blocks] for prev_hash in block.previous_hashes):
                if self.blocks:  # Если это не genesis блок
                    return False
            
            # Добавляем блок
            self.blocks.append(block)
            
            # Обновляем tips
            self.tips.difference_update(block.previous_hashes)
            self.tips.add(block.hash)
            
            return True
    
    def get_tips(self) -> List[str]:
        """Возвращает текущие tips DAG"""
        with self.lock:
            return list(self.tips)
    
    def get_block(self, block_hash: str) -> DAGBlock:
        """Находит блок по хэшу"""
        with self.lock:
            for block in self.blocks:
                if block.hash == block_hash:
                    return block
            return None
    
    def get_blocks_since(self, timestamp: float) -> List[DAGBlock]:
        """Возвращает блоки начиная с указанного времени"""
        with self.lock:
            return [block for block in self.blocks if block.timestamp >= timestamp]
    
    def get_all_transactions(self) -> List:
        """Возвращает все транзакции в шарде"""
        with self.lock:
            transactions = []
            for block in self.blocks:
                transactions.extend(block.transactions)
            return transactions
    
    def get_shard_stats(self) -> dict:
        """Возвращает статистику шарда"""
        with self.lock:
            return {
                "shard_id": self.shard_id,
                "block_count": len(self.blocks),
                "transaction_count": len(self.get_all_transactions()),
                "tips_count": len(self.tips),
                "latest_block": self.blocks[-1].hash if self.blocks else None
            }
