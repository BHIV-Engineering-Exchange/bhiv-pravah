"""
Initialization module for the integration adapters package.

This module exports all the adapter classes to make them easily importable."""

from .base_adapter import BaseIntegrationAdapter
from .artha_adapter import ArthaAdapter
from .karya_adapter import KaryaAdapter
from .insightflow_adapter import InsightFlowAdapter
from .bucket_adapter import BucketAdapter

__all__ = [
    'BaseIntegrationAdapter',
    'ArthaAdapter',
    'KaryaAdapter',
    'InsightFlowAdapter',
    'BucketAdapter'
]

def get_all_adapters():
    """
    Returns a dictionary mapping adapter names to their classes.
    This is useful for dynamic adapter loading.
    """
    return {
        'artha': ArthaAdapter,
        'karya': KaryaAdapter,
        'insightflow': InsightFlowAdapter,
        'bucket': BucketAdapter
    }
