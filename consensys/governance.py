import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ProposalType(Enum):
    PARAMETER_CHANGE = "parameter_change"
    REPUTATION_WEIGHTS = "reputation_weights"
    VALIDATOR_SLASHING = "validator_slashing"
    NETWORK_UPGRADE = "network_upgrade"

@dataclass
class GovernanceProposal:
    id: str
    proposal_type: ProposalType
    title: str
    description: str
    proposed_by: str  # validator address
    parameters: Dict
    voting_start: float
    voting_end: float
    votes_for: int = 0
    votes_against: int = 0
    executed: bool = False

class Governance:
    def __init__(self, validator_manager):
        self.validator_manager = validator_manager
        self.proposals: Dict[str, GovernanceProposal] = {}
        self.voted_validators = set()
    
    def create_proposal(self, proposal_type: ProposalType, title: str, 
                       description: str, proposed_by: str, parameters: Dict,
                       voting_duration_hours: int = 24) -> str:
        """Создает новое предложение для governance"""
        proposal_id = f"prop_{int(time.time())}_{proposed_by[:8]}"
        
        proposal = GovernanceProposal(
            id=proposal_id,
            proposal_type=proposal_type,
            title=title,
            description=description,
            proposed_by=proposed_by,
            parameters=parameters,
            voting_start=time.time(),
            voting_end=time.time() + (voting_duration_hours * 3600)
        )
        
        self.proposals[proposal_id] = proposal
        return proposal_id
    
    def vote_on_proposal(self, proposal_id: str, validator_address: str, 
                        vote_for: bool) -> bool:
        """Голосование по предложению"""
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        
        # Проверяем, что голосование активно
        if time.time() < proposal.voting_start or time.time() > proposal.voting_end:
            return False
        
        # Проверяем, что валидатор еще не голосовал
        vote_key = f"{proposal_id}_{validator_address}"
        if vote_key in self.voted_validators:
            return False
        
        # Записываем голос
        if vote_for:
            proposal.votes_for += 1
        else:
            proposal.votes_against += 1
        
        self.voted_validators.add(vote_key)
        
        # Записываем участие в метриках
        self.validator_manager.record_governance_vote(validator_address, proposal_id)
        
        # Проверяем, можно ли исполнить предложение
        self._check_proposal_execution(proposal_id)
        
        return True
    
    def _check_proposal_execution(self, proposal_id: str):
        """Проверяет и исполняет предложение при достижении кворума"""
        proposal = self.proposals[proposal_id]
        
        if time.time() < proposal.voting_end:
            return  # Голосование еще активно
        
        total_votes = proposal.votes_for + proposal.votes_against
        if total_votes == 0:
            return  # Никто не проголосовал
        
        approval_rate = proposal.votes_for / total_votes
        
        # Исполняем если за проголосовало >66%
        if approval_rate > 0.66 and not proposal.executed:
            self._execute_proposal(proposal)
            proposal.executed = True
    
    def _execute_proposal(self, proposal: GovernanceProposal):
        """Исполняет approved proposal"""
        if proposal.proposal_type == ProposalType.REPUTATION_WEIGHTS:
            # Изменение весов метрик в репутационной системе
            new_weights = proposal.parameters.get("metric_weights", {})
            self.validator_manager.reputation_system.metric_weights.update(new_weights)
            print(f"Updated reputation weights: {new_weights}")
        
        elif proposal.proposal_type == ProposalType.VALIDATOR_SLASHING:
            # Наказание валидатора
            validator_address = proposal.parameters.get("validator_address")
            penalty_severity = proposal.parameters.get("penalty_severity", 0.05)
            reason = proposal.parameters.get("reason", "Governance decision")
            
            self.validator_manager.penalize_validator(
                validator_address, reason, penalty_severity
            )
            print(f"Validator {validator_address} slashed via governance")
        
        elif proposal.proposal_type == ProposalType.PARAMETER_CHANGE:
            # Изменение параметров сети
            parameter_name = proposal.parameters.get("parameter_name")
            new_value = proposal.parameters.get("new_value")
            
            # Здесь будет логика изменения параметров блокчейна
            print(f"Changed parameter {parameter_name} to {new_value}")
