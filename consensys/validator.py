import time
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from .reputation import ReputationSystem, MetricType
from .oracles import QualityOracle
import threading

@dataclass
class Validator:
    address: str
    sphincs_sk: object
    ntru_sk: object 
    stake: int
    total_stake: int = 0
    github_username: Optional[str] = None
    last_active: float = 0
    is_active: bool = True

class ValidatorManager:
    def __init__(self, min_stake: int):
        self.validators: List[Validator] = []
        self.min_stake = min_stake
        self.reputation_system = ReputationSystem()
        self.quality_oracle = QualityOracle()
        self.lock = threading.Lock()
        
        # Запускаем фоновое обновление метрик
        self.running = True
        threading.Thread(target=self._metrics_update_loop, daemon=True).start()
    
    def add_validator(self, address: str, sphincs_sk, ntru_sk, stake: int, 
                     github_username: Optional[str] = None):
        """Добавляет валидатора с начальной репутацией"""
        if stake < self.min_stake:
            raise ValueError("Insufficient stake")
        
        validator = Validator(
            address=address,
            sphincs_sk=sphincs_sk,
            ntru_sk=ntru_sk,
            stake=stake,
            github_username=github_username,
            last_active=time.time(),
            is_active=True
        )
        
        with self.lock:
            self.validators.append(validator)
        
        # Инициализируем метрики
        self._initialize_validator_metrics(validator)
    
    def _initialize_validator_metrics(self, validator: Validator):
        """Инициализирует начальные метрики для валидатора"""
        # Начальный аптайм
        self.reputation_system.record_uptime(validator.address, True)
        
        # Загружаем внешние метрики
        if validator.github_username:
            external_metrics = self.quality_oracle.fetch_validator_metrics(
                validator.address, validator.github_username
            )
            
            # Добавляем code contributions
            if "github_contributions" in external_metrics:
                gh_data = external_metrics["github_contributions"]
                self.reputation_system.add_code_contribution(
                    validator.address,
                    gh_data["lines_added"],
                    gh_data["lines_removed"],
                    is_core_contribution=True
                )
            
            # Добавляем community metrics
            if "forum_activity" in external_metrics:
                forum_data = external_metrics["forum_activity"]
                self.reputation_system.add_community_metric(
                    validator.address,
                    forum_data["helpful_answers"] / max(forum_data["posts_count"], 1),
                    forum_data["reputation_score"] / 100.0
                )
    
    def select_validator(self) -> Optional[Validator]:
        """Выбирает валидатора по алгоритму DPoQS"""
        with self.lock:
            active_validators = [v for v in self.validators if v.is_active]
            
            if not active_validators:
                return None
            
            # Рассчитываем комбинированный score для каждого валидатора
            validator_scores = []
            for validator in active_validators:
                reputation_score = self.reputation_system.get_validator_score(validator.address)
                stake_score = min(1.0, validator.stake / (self.min_stake * 10))  # Нормализуем стейк
                
                # Комбинированный score: 70% репутация, 30% стейк
                combined_score = (reputation_score * 0.7) + (stake_score * 0.3)
                
                validator_scores.append((validator, combined_score))
            
            # Выбираем валидатора с наивысшим score
            selected_validator = max(validator_scores, key=lambda x: x[1])[0]
            
            # Обновляем время активности
            selected_validator.last_active = time.time()
            
            return selected_validator
    
    def record_block_creation(self, validator_address: str, block_hash: str, 
                            accepted: bool, propagation_time: float):
        """Записывает создание блока для метрик"""
        self.reputation_system.record_block_quality(
            validator_address, block_hash, accepted, propagation_time
        )
    
    def record_uptime(self, validator_address: str, is_online: bool):
        """Записывает статус онлайн/оффлайн"""
        self.reputation_system.record_uptime(validator_address, is_online)
        
        # Обновляем статус валидатора
        with self.lock:
            for validator in self.validators:
                if validator.address == validator_address:
                    validator.is_active = is_online
                    break
    
    def record_governance_vote(self, validator_address: str, proposal_id: str):
        """Записывает участие в голосовании"""
        self.reputation_system.record_governance_participation(
            validator_address, proposal_id, True
        )
    
    def penalize_validator(self, validator_address: str, penalty_reason: str, 
                          penalty_severity: float = 0.05):
        """Наказывает валидатора (сланкинг)"""
        with self.lock:
            for validator in self.validators:
                if validator.address == validator_address:
                    penalty_amount = int(validator.stake * penalty_severity)
                    validator.stake -= penalty_amount
                    
                    # Также снижаем репутацию
                    self.reputation_system.add_metric(
                        validator_address,
                        self.reputation_system.create_metric(
                            MetricType.BLOCK_QUALITY,
                            0.1,  # Сильное снижение за проступок
                            "penalty"
                        )
                    )
                    
                    print(f"Validator {validator_address} penalized: {penalty_reason}, "
                          f"amount: {penalty_amount}")
                    break
    
    def reward_validator(self, validator_address: str, reward_amount: int):
        """Вознаграждает валидатора"""
        with self.lock:
            for validator in self.validators:
                if validator.address == validator_address:
                    validator.stake += reward_amount
                    break
    
    def get_validator_stats(self, validator_address: str) -> Dict:
        """Возвращает статистику валидатора"""
        reputation = self.reputation_system.get_validator_score(validator_address)
        
        with self.lock:
            validator = next((v for v in self.validators if v.address == validator_address), None)
            if validator:
                return {
                    "address": validator.address,
                    "stake": validator.stake,
                    "reputation_score": reputation,
                    "is_active": validator.is_active,
                    "last_active": validator.last_active
                }
        
        return {}
    
    def _metrics_update_loop(self):
        """Фоновое обновление метрик"""
        while self.running:
            try:
                with self.lock:
                    active_validators = self.validators.copy()
                
                for validator in active_validators:
                    if validator.is_active:
                        # Обновляем метрики сети
                        self.reputation_system.record_network_health(
                            validator.address,
                            peers_connected=25,  # В реальности получать из сети
                            bandwidth_usage=500  # МБ/с
                        )
                        
                        # Обновляем внешние метрики раз в час
                        if int(time.time()) % 3600 == 0:
                            self._update_external_metrics(validator)
                
                time.sleep(60)  # Обновляем каждую минуту
                
            except Exception as e:
                print(f"Metrics update error: {e}")
                time.sleep(300)  # Ждём 5 минут при ошибке
    
    def _update_external_metrics(self, validator: Validator):
        """Обновляет внешние метрики для валидатора"""
        external_metrics = self.quality_oracle.fetch_validator_metrics(
            validator.address, validator.github_username
        )
        
        # Обновляем code contributions
        if "github_contributions" in external_metrics:
            gh_data = external_metrics["github_contributions"]
            if gh_data["commit_count"] > 0:
                self.reputation_system.add_code_contribution(
                    validator.address,
                    gh_data["lines_added"],
                    gh_data["lines_removed"],
                    is_core_contribution=True
                )
