"""
Workflow Executor Integration Module
Provides fire-and-forget clients for Bucket and Karma integration
"""

from integration.bucket_client import bucket_client
from integration.karma_client import karma_client

__all__ = ['bucket_client', 'karma_client']
