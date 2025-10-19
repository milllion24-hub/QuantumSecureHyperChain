import time
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import statistics
from dataclasses import dataclass
from enum import Enum

class MetricType(Enum):
    UPTIME = "uptime"
    BLOCK_QUALITY = "block_quality"
    GOVERNANCE = "governance"
    CODE_CONTRIBUTION = "code_contribution"
    COMMUNITY = "community"
    NETWORK_HEALTH = "network_health"

@dataclass
class QualityMetric:
    metric_type: MetricType
    value: float
    weight: float
    timestamp: float
    source: str  # "system", "oracle", "voting"

class ReputationSystem:
    def __init__(self):
        self.validator_metrics = defaultdict(list)
        self.validator_scores = defaultdict(float)
        self.uptime_history = defaultdict(lambda: deque(maxlen=1000))
        self.voting_records = defaultdict(list)
        
        # Веса метрик (можно настраивать через governance)
        self.metric_weights = {
            MetricType.UPTIME: 0.25,
            MetricType.BLOCK_QUALITY: 0.30,
            MetricType.GOVERNANCE: 0.15,
            MetricType.CODE_CONTRIBUTION: 0.10,
            MetricType.COMMUNITY: 0.10,
            MetricType.NETWORK_HEALTH: 0.10
        }
    
    def add_metric(self, validator_address: str, metric: QualityMetric):
        """Добавляет метрику для валидатора"""
        self.validator_metrics[validator_address].append(metric)
        self._recalculate_score(validator_address)
    
    def record_uptime(self, validator_address: str, is_online: bool):
        """Записывает аптайм валидатора"""
        self.uptime_history[validator_address].append(1 if is_online else 0)
        
        # Рассчитываем аптайм за последние 24 часа
        if len(self.uptime_history[validator_address]) > 0:
            uptime = sum(self.uptime_history[validator_address]) / len(self.uptime_history[validator_address])
            metric = QualityMetric(
                metric_type=MetricType.UPTIME,
                value=uptime,
                weight=self.metric_weights[MetricType.UPTIME],
                timestamp=time.time(),
                source="system"
            )
            self.add_metric(validator_address, metric)
    
    def record_block_quality(self, validator_address: str, block_hash: str, 
                           accepted: bool, propagation_time: float):
        """Записывает качество созданного блока"""
        quality_score = 0.8 if accepted else 0.2  # Базовый score
        quality_score *= min(1.0, 1.0 / (propagation_time + 0.1))  # Учёт скорости распространения
        
        metric = QualityMetric(
            metric_type=MetricType.BLOCK_QUALITY,
            value=quality_score,
            weight=self.metric_weights[MetricType.BLOCK_QUALITY],
            timestamp=time.time(),
            source="system"
        )
        self.add_metric(validator_address, metric)
    
    def record_governance_participation(self, validator_address: str, 
                                      proposal_id: str, voted: bool):
        """Записывает участие в governance"""
        participation = 1.0 if voted else 0.0
        metric = QualityMetric(
            metric_type=MetricType.GOVERNANCE,
            value=participation,
            weight=self.metric_weights[MetricType.GOVERNANCE],
            timestamp=time.time(),
            source="system"
        )
        self.add_metric(validator_address, metric)
    
    def add_code_contribution(self, validator_address: str, lines_added: int,
                            lines_removed: int, is_core_contribution: bool):
        """Добавляет метрику вклада в код"""
        contribution_score = min(1.0, (lines_added + lines_removed) / 1000)
        if is_core_contribution:
            contribution_score *= 2.0  # Усиление за core-вклад
        
        metric = QualityMetric(
            metric_type=MetricType.CODE_CONTRIBUTION,
            value=min(1.0, contribution_score),
            weight=self.metric_weights[MetricType.CODE_CONTRIBUTION],
            timestamp=time.time(),
            source="oracle"
        )
        self.add_metric(validator_address, metric)
    
    def add_community_metric(self, validator_address: str, help_score: float,
                           content_quality: float):
        """Добавляет метрику участия в комьюнити"""
        community_score = (help_score * 0.6 + content_quality * 0.4)
        
        metric = QualityMetric(
            metric_type=MetricType.COMMUNITY,
            value=community_score,
            weight=self.metric_weights[MetricType.COMMUNITY],
            timestamp=time.time(),
            source="oracle"
        )
        self.add_metric(validator_address, metric)
    
    def record_network_health(self, validator_address: str, peers_connected: int,
                            bandwidth_usage: float):
        """Записывает метрики здоровья сети"""
        health_score = min(1.0, peers_connected / 50) * 0.7  # До 50 пиров = 100%
        health_score += min(1.0, bandwidth_usage / 1000) * 0.3  # До 1 ГБ/с = 100%
        
        metric = QualityMetric(
            metric_type=MetricType.NETWORK_HEALTH,
            value=health_score,
            weight=self.metric_weights[MetricType.NETWORK_HEALTH],
            timestamp=time.time(),
            source="system"
        )
        self.add_metric(validator_address, metric)
    
    def _recalculate_score(self, validator_address: str):
        """Пересчитывает общий score валидатора"""
        recent_metrics = self._get_recent_metrics(validator_address, hours=24)
        
        if not recent_metrics:
            self.validator_scores[validator_address] = 0.0
            return
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric_type in MetricType:
            type_metrics = [m for m in recent_metrics if m.metric_type == metric_type]
            if type_metrics:
                # Берем среднее по метрикам этого типа
                avg_value = statistics.mean([m.value for m in type_metrics])
                weighted_sum += avg_value * self.metric_weights[metric_type]
                total_weight += self.metric_weights[metric_type]
        
        if total_weight > 0:
            self.validator_scores[validator_address] = weighted_sum / total_weight
        else:
            self.validator_scores[validator_address] = 0.0
    
    def _get_recent_metrics(self, validator_address: str, hours: int = 24) -> List[QualityMetric]:
        """Возвращает метрики за последние N часов"""
        cutoff_time = time.time() - (hours * 3600)
        return [
            metric for metric in self.validator_metrics[validator_address]
            if metric.timestamp >= cutoff_time
        ]
    
    def get_validator_score(self, validator_address: str) -> float:
        """Возвращает текущий score валидатора"""
        return self.validator_scores.get(validator_address, 0.0)
    
    def get_top_validators(self, count: int = 10) -> List[Tuple[str, float]]:
        """Возвращает топ валидаторов по репутации"""
        scored_validators = [(addr, score) for addr, score in self.validator_scores.items()]
        return sorted(scored_validators, key=lambda x: x[1], reverse=True)[:count]
