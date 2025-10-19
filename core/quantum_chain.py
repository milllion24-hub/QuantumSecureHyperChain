import time
import threading
import json
import os
from typing import List, Dict, Optional

# Импорты из пакета
from . import crypto, transactions, dag, consensus, network, monitoring

class QuantumSecureHyperChain:
    def __init__(self, config_path: str = "config/network_config.json"):
        # Загрузка конфигурации
        self.load_config(config_path)
        
        # Инициализация компонентов
        self.crypto = crypto.QuantumCrypto()
        self.transactions_pool = transactions.TransactionPool()
        self.dag_shards = [dag.DAGShard(shard_id=i) for i in range(self.sharding_factor)]
        self.validators = consensus.ValidatorManager(self.min_stake)
        self.network = network.P2PNetwork(self.port)
        self.monitor = monitoring.ThreatDetector(penalty_pool=self.transactions_pool)
        
        # DPoQS специфичные атрибуты
        self.validator_performance = {}
        self.propagation_times = {}
        self.block_times = {}
        
        # Локи для потокобезопасности
        self.pool_lock = threading.Lock()
        self.shard_lock = threading.Lock()
        self.validator_lock = threading.Lock()
        
        # Запуск процессов
        self.start_background_services()

    def load_config(self, config_path: str):
        """Загрузка конфигурации из JSON"""
        defaults = {
            "tps_target": 5_000_000,
            "block_time": 0.5,
            "sharding_factor": 4,
            "min_stake": 100_000,
            "port": 8000,
            "max_validators": 100,
            "reputation_update_interval": 60
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                for key, default_val in defaults.items():
                    setattr(self, key, config.get(key, default_val))
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки конфигурации: {e}. Используем defaults.")
                self.__dict__.update(defaults)
        else:
            print("Конфиг-файл не найден. Используем defaults.")
            self.__dict__.update(defaults)

    def start_background_services(self):
        """Запуск фоновых сервисов DPoQS"""
        threading.Thread(target=self.block_creation_loop, daemon=True).start()
        threading.Thread(target=self.dag_synchronization, daemon=True).start()
        threading.Thread(target=self.uptime_monitoring, daemon=True).start()
        threading.Thread(target=self.reputation_update_loop, daemon=True).start()
        threading.Thread(target=lambda: self.monitor.start(), daemon=True).start()

    def block_creation_loop(self):
        """Основной цикл создания блоков"""
        while True:
            try:
                self.create_block()
                time.sleep(self.block_time)
            except Exception as e:
                print(f"Error in block creation: {e}")
                time.sleep(1)

    def select_shard(self, transaction_hash: str = None):
        """Выбор шарда для нового блока"""
        if transaction_hash:
            # Детерминированный выбор на основе хэша транзакции
            shard_index = int(transaction_hash[:8], 16) % self.sharding_factor
        else:
            # Случайный выбор для пустых блоков
            import random
            shard_index = random.randint(0, self.sharding_factor - 1)
        
        with self.shard_lock:
            return self.dag_shards[shard_index]

    def create_block(self):
        """Создание блока через DPoQS консенсус"""
        shard = self.select_shard()
        
        with self.pool_lock:
            transactions_list = self.transactions_pool.get_batch(10)
        
        # Выбор валидатора через DPoQS
        validator = self.validators.select_validator()
        
        if not validator:
            print("No active validators available for block creation")
            return
        
        # Создаем блок
        block = dag.DAGBlock(
            shard_id=shard.shard_id,
            transactions=transactions_list,
            miner=validator.address,
            previous_hashes=shard.get_tips()
        )
        
        # Подписываем блок
        start_time = time.time()
        try:
            block.add_signature("sphincs", 
                self.crypto.sign(block.hash.encode(), validator.sphincs_sk, "sphincs"))
            block.add_signature("ntru", 
                self.crypto.sign(block.hash.encode(), validator.ntru_sk, "ntru"))
        except Exception as e:
            print(f"Block signing error: {e}")
            return
        
        # Добавляем в DAG
        with self.shard_lock:
            if shard.add_block(block):
                propagation_time = time.time() - start_time
                
                # Записываем метрики качества блока в DPoQS
                self.validators.record_block_creation(
                    validator.address, 
                    block.hash, 
                    True,  # accepted
                    propagation_time
                )
                
                # Сохраняем время для метрик
                self.propagation_times[block.hash] = propagation_time
                self.block_times[block.hash] = time.time()
                
                # Вознаграждаем валидатора
                self.validators.reward_validator(validator.address, 10)
                
                # Broadcast блока
                self.network.broadcast_block(block)
                
                print(f"Block {block.hash[:16]} created by {validator.address[:16]} "
                      f"in shard {shard.shard_id}, propagation: {propagation_time:.3f}s")

    def validate_incoming_block(self, block: dag.DAGBlock) -> bool:
        """Валидация входящего блока с учётом DPoQS"""
        try:
            # Получаем публичный ключ валидатора
            validator_pk = self.get_validator_public_key(block.miner)
            if not validator_pk:
                print(f"Unknown validator: {block.miner}")
                return False
            
            # Проверяем подписи
            sphincs_valid = self.crypto.verify(
                block.hash.encode(),
                block.signatures.get("sphincs", b""),
                validator_pk,
                "sphincs"
            )
            
            if not sphincs_valid:
                print(f"Invalid SPHINCS signature for block {block.hash[:16]}")
                self.validators.penalize_validator(
                    block.miner, 
                    "Invalid SPHINCS signature", 
                    0.05
                )
                return False
            
            # Проверяем NTRU подпись
            ntru_valid = self.crypto.verify(
                block.hash.encode(),
                block.signatures.get("ntru", b""),
                validator_pk,
                "ntru"
            )
            
            if not ntru_valid:
                print(f"Invalid NTRU signature for block {block.hash[:16]}")
                self.validators.penalize_validator(
                    block.miner, 
                    "Invalid NTRU signature", 
                    0.05
                )
                return False
            
            # Обновляем метрики валидатора
            propagation_time = self.propagation_times.get(block.hash, 1.0)
            self.validators.record_block_creation(
                block.miner, block.hash, True, propagation_time
            )
            
            return True
            
        except Exception as e:
            print(f"Block validation error: {e}")
            return False

    def get_validator_public_key(self, validator_address: str):
        """Получает публичный ключ валидатора"""
        with self.validator_lock:
            for validator in self.validators.validators:
                if validator.address == validator_address:
                    # В реальной реализации здесь будет получение публичного ключа
                    # Для демо возвращаем заглушку
                    return f"public_key_{validator_address}"
        return None

    def dag_synchronization(self):
        """Синхронизация DAG между шардами"""
        while True:
            try:
                # В реальной реализации здесь будет сложная логика синхронизации
                # между шардами и нодами
                time.sleep(10)
            except Exception as e:
                print(f"DAG synchronization error: {e}")
                time.sleep(30)

    def uptime_monitoring(self):
        """Мониторинг аптайма валидаторов для DPoQS"""
        while True:
            try:
                # Проверяем активность валидаторов по последним блокам
                current_time = time.time()
                
                for shard in self.dag_shards:
                    recent_blocks = shard.blocks[-5:]  # Последние 5 блоков
                    for block in recent_blocks:
                        validator = block.miner
                        # Считаем валидатора онлайн если он создал блок в последние 5 минут
                        is_online = (current_time - block.timestamp) < 300
                        self.validators.record_uptime(validator, is_online)
                
                time.sleep(60)  # Проверяем каждую минуту
                
            except Exception as e:
                print(f"Uptime monitoring error: {e}")
                time.sleep(300)

    def reputation_update_loop(self):
        """Фоновое обновление репутации DPoQS"""
        while True:
            try:
                # Обновляем метрики сети для всех активных валидаторов
                active_validators = [v for v in self.validators.validators if v.is_active]
                
                for validator in active_validators:
                    # Имитируем метрики сети
                    self.validators.reputation_system.record_network_health(
                        validator.address,
                        peers_connected=25,
                        bandwidth_usage=500
                    )
                
                time.sleep(self.reputation_update_interval)
                
            except Exception as e:
                print(f"Reputation update error: {e}")
                time.sleep(300)

    def add_transaction(self, transaction):
        """Добавление транзакции в пул"""
        with self.pool_lock:
            self.transactions_pool.add_transaction(transaction)

    def get_blockchain_stats(self) -> Dict:
        """Возвращает статистику блокчейна"""
        total_blocks = sum(len(shard.blocks) for shard in self.dag_shards)
        total_transactions = sum(len(shard.get_all_transactions()) for shard in self.dag_shards)
        
        active_validators = len([v for v in self.validators.validators if v.is_active])
        total_validators = len(self.validators.validators)
        
        return {
            "total_blocks": total_blocks,
            "total_transactions": total_transactions,
            "active_validators": active_validators,
            "total_validators": total_validators,
            "sharding_factor": self.sharding_factor,
            "tps_target": self.tps_target
        }

    def get_validator_info(self, validator_address: str) -> Optional[Dict]:
        """Возвращает информацию о валидаторе"""
        return self.validators.get_validator_stats(validator_address)
