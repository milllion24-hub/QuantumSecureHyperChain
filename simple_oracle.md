# oracle.py
import requests
import time
from typing import Optional, Dict
import hashlib

class GitHubOracle:
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token
        self.base_url = "https://api.github.com"
    
    def get_contributions(self, github_username: str, repo_owner: str, repo_name: str) -> Dict:
        """Получает данные о contributions из GitHub"""
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"
        
        try:
            # Получаем commits
            commits_url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/commits"
            params = {"author": github_username}
            response = requests.get(commits_url, headers=headers, params=params)
            
            if response.status_code == 200:
                commits = response.json()
                return {
                    "commit_count": len(commits),
                    "lines_added": sum(c.get('stats', {}).get('additions', 0) for c in commits),
                    "lines_removed": sum(c.get('stats', {}).get('deletions', 0) for c in commits),
                    "last_commit": commits[0].get('commit', {}).get('author', {}).get('date') if commits else None
                }
        except Exception as e:
            print(f"GitHub Oracle error: {e}")
        
        return {"commit_count": 0, "lines_added": 0, "lines_removed": 0}

class CommunityOracle:
    def __init__(self, forum_api_url: str):
        self.forum_api_url = forum_api_url
    
    def get_forum_activity(self, user_identifier: str) -> Dict:
        """Получает активность на форумах (заглушка - в реальности API форума)"""
        # В реальной реализации здесь будут запросы к API форума
        return {
            "posts_count": 15,
            "helpful_answers": 8,
            "reputation_score": 85.5
        }

class QualityOracle:
    def __init__(self):
        self.github_oracle = GitHubOracle()
        self.community_oracle = CommunityOracle("https://forum.quantumchain.com/api")
    
    def fetch_validator_metrics(self, validator_address: str, github_username: Optional[str] = None) -> Dict:
        """Собирает метрики из внешних источников"""
        metrics = {}
        
        if github_username:
            # GitHub contributions
            gh_data = self.github_oracle.get_contributions(github_username, "quantum-chain", "core")
            metrics["github_contributions"] = gh_data
        
        # Forum activity (используем хэш адреса как идентификатор)
        forum_id = hashlib.sha256(validator_address.encode()).hexdigest()[:16]
        forum_data = self.community_oracle.get_forum_activity(forum_id)
        metrics["forum_activity"] = forum_data
        
        return metrics
