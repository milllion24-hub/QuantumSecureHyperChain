import pytest
import time
from src.consensus.validator import ValidatorManager
from src.consensus.reputation import ReputationSystem, MetricType
from src.crypto.quantum_crypto import QuantumCrypto

def test_dpoqs_validator_selection():
    """Тест выбора валидатора по DPoQS"""
    crypto = QuantumCrypto()
    validator_manager = ValidatorManager(min_stake=100000)
    
    # Добавляем валидаторов с разными характеристиками
    sphincs_sk1, _ = crypto.generate_keypair("sphincs")
    ntru_sk1, _ = crypto.generate_keypair("ntru")
    
    sphincs_sk2, _ = crypto.generate_keypair("sphincs") 
    ntru_sk2, _ = crypto.generate_keypair("ntru")
    
    # Валидатор 1: большой стейк, но низкая репутация
    validator_manager.add_validator("val1", sphincs_sk1, ntru_sk1, 500000)
    
    # Валидатор 2: средний стейк, но высокая репутация
    validator_manager.add_validator("val2", sphincs_sk2, ntru_sk2, 200000, "good_validator")
    
    # Имитируем хорошие метрики для val2
    validator_manager.reputation_system.record_uptime("val2", True)
    validator_manager.reputation_system.record_block_quality("val2", "block1", True, 0.1)
    validator_manager.reputation_system.add_code_contribution("val2", 1000, 200, True)
    
    # DPoQS должен выбрать val2 из-за высокой репутации
    selected = validator_manager.select_validator()
    assert selected.address == "val2"

def test_reputation_calculation():
    """Тест расчета репутации"""
    rep_system = ReputationSystem()
    
    # Добавляем метрики для валидатора
    rep_system.record_uptime("val1", True)
    rep_system.record_block_quality("val1", "block1", True, 0.1)
    rep_system.record_governance_participation("val1", "prop1", True)
    
    score = rep_system.get_validator_score("val1")
    assert 0 < score <= 1.0

def test_penalty_system():
    """Тест системы наказаний"""
    crypto = QuantumCrypto()
    validator_manager = ValidatorManager(min_stake=100000)
    
    sphincs_sk, _ = crypto.generate_keypair("sphincs")
    ntru_sk, _ = crypto.generate_keypair("ntru")
    
    validator_manager.add_validator("val1", sphincs_sk, ntru_sk, 200000)
    
    initial_stake = validator_manager.validators[0].stake
    validator_manager.penalize_validator("val1", "test penalty", 0.1)
    
    assert validator_manager.validators[0].stake < initial_stake

if __name__ == "__main__":
    pytest.main([__file__])
