#!/usr/bin/env python3
"""
Comprehensive test suite for AI Agent core functionality
"""

import pytest
import pandas as pd
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys
sys.path.append('..')

# Import modules to test
import agent
import chatbot_agent
from human_review import HumanReviewSystem

class TestAgentCore:
    """Test the main agent logic"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.test_dir = tempfile.mkdtemp()
        self.original_files = {
            'RETURNS_FILE': agent.RETURNS_FILE,
            'RESTOCK_FILE': agent.RESTOCK_FILE,
            'LOG_FILE': agent.LOG_FILE
        }
        
        # Create test data
        self.test_returns_data = pd.DataFrame({
            'ProductID': ['A101', 'B202', 'C303', 'D404'],
            'ReturnQuantity': [6, 3, 15, 2]
        })
        
        # Set up test files
        agent.RETURNS_FILE = os.path.join(self.test_dir, 'test_returns.xlsx')
        agent.RESTOCK_FILE = os.path.join(self.test_dir, 'test_restock.xlsx')
        agent.LOG_FILE = os.path.join(self.test_dir, 'test_logs.csv')
        
        self.test_returns_data.to_excel(agent.RETURNS_FILE, index=False)
    
    def teardown_method(self):
        """Clean up test environment after each test"""
        # Restore original file paths
        for key, value in self.original_files.items():
            setattr(agent, key, value)
        
        # Clean up test directory
        shutil.rmtree(self.test_dir)
    
    def test_sense_function(self):
        """Test the sense function reads data correctly"""
        result = agent.sense()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        assert 'ProductID' in result.columns
        assert 'ReturnQuantity' in result.columns
    
    def test_plan_function(self):
        """Test the plan function identifies correct restocks"""
        df = self.test_returns_data
        result = agent.plan(df)
        
        # Should identify A101 (6) and C303 (15) as needing restock (>5)
        assert len(result) == 2
        
        product_ids = [item['ProductID'] for item in result]
        assert 'A101' in product_ids
        assert 'C303' in product_ids
        assert 'B202' not in product_ids  # Only 3 returns
        assert 'D404' not in product_ids  # Only 2 returns
    
    def test_plan_function_edge_cases(self):
        """Test plan function with edge cases"""
        # Empty data
        empty_df = pd.DataFrame(columns=['ProductID', 'ReturnQuantity'])
        result = agent.plan(empty_df)
        assert len(result) == 0
        
        # All below threshold
        low_returns = pd.DataFrame({
            'ProductID': ['X001', 'X002'],
            'ReturnQuantity': [1, 2]
        })
        result = agent.plan(low_returns)
        assert len(result) == 0
        
        # Exactly at threshold
        threshold_returns = pd.DataFrame({
            'ProductID': ['Y001'],
            'ReturnQuantity': [5]
        })
        result = agent.plan(threshold_returns)
        assert len(result) == 0  # Should be > threshold, not >=
    
    @patch('agent.review_system')
    def test_act_function_high_confidence(self, mock_review_system):
        """Test act function with high confidence decisions"""
        mock_review_system.requires_human_review.return_value = False
        
        restocks = [
            {'ProductID': 'A101', 'RestockQuantity': 6},
            {'ProductID': 'C303', 'RestockQuantity': 8}
        ]
        
        agent.act(restocks)
        
        # Check if restock file was created
        assert os.path.exists(agent.RESTOCK_FILE)
        
        # Check if log file was created
        assert os.path.exists(agent.LOG_FILE)
        
        # Verify restock data
        restock_df = pd.read_excel(agent.RESTOCK_FILE)
        assert len(restock_df) == 2
        assert 'A101' in restock_df['ProductID'].values
        assert 'C303' in restock_df['ProductID'].values
    
    @patch('agent.review_system')
    def test_act_function_low_confidence(self, mock_review_system):
        """Test act function with low confidence decisions"""
        mock_review_system.requires_human_review.return_value = True
        mock_review_system.submit_for_review.return_value = "test_review_id"
        
        restocks = [
            {'ProductID': 'A101', 'RestockQuantity': 25}  # High quantity
        ]
        
        agent.act(restocks)
        
        # Should not create restock file for low confidence
        assert not os.path.exists(agent.RESTOCK_FILE)
        
        # Should submit for review
        mock_review_system.submit_for_review.assert_called_once()
    
    def test_threshold_configuration(self):
        """Test that threshold can be configured"""
        original_threshold = agent.THRESHOLD
        
        # Test with different threshold
        agent.THRESHOLD = 10
        
        df = pd.DataFrame({
            'ProductID': ['TEST001'],
            'ReturnQuantity': [8]
        })
        
        result = agent.plan(df)
        assert len(result) == 0  # Should not trigger with threshold 10
        
        # Restore original threshold
        agent.THRESHOLD = original_threshold

class TestChatbotLogic:
    """Test the chatbot logic"""
    
    def setup_method(self):
        """Set up test data for chatbot"""
        # Create test data
        orders_data = pd.DataFrame({
            'OrderID': [101, 102, 103],
            'Status': ['Shipped', 'Delivered', 'Processing']
        })
        
        restocks_data = pd.DataFrame({
            'ProductID': ['A101', 'B202'],
            'RestockQuantity': [10, 5]
        })
        
        # Patch the dataframes in chatbot_agent
        chatbot_agent.orders_df = orders_data
        chatbot_agent.restocks_df = restocks_data
    
    def test_extract_order_id(self):
        """Test order ID extraction from messages"""
        assert chatbot_agent.extract_order_id("Where is my order #123?") == 123
        assert chatbot_agent.extract_order_id("order 456") == 456
        assert chatbot_agent.extract_order_id("ORDER 789") == 789
        assert chatbot_agent.extract_order_id("no order here") is None
        assert chatbot_agent.extract_order_id("") is None
    
    def test_extract_product_id(self):
        """Test product ID extraction from messages"""
        assert chatbot_agent.extract_product_id("When will product A101 be restocked?") == "A101"
        assert chatbot_agent.extract_product_id("Product b202 status") == "B202"
        assert chatbot_agent.extract_product_id("PRODUCT C303") == "C303"
        assert chatbot_agent.extract_product_id("no product here") is None
        assert chatbot_agent.extract_product_id("") is None
    
    @patch('chatbot_agent.review_system')
    def test_order_status_query(self, mock_review_system):
        """Test order status queries"""
        mock_review_system.requires_human_review.return_value = False
        
        response = chatbot_agent.chatbot_response("Where is my order #101?")
        assert "Shipped" in response
        assert "#101" in response
        
        # Test non-existent order
        response = chatbot_agent.chatbot_response("Where is my order #999?")
        assert "couldn't find" in response or "not found" in response
    
    @patch('chatbot_agent.review_system')
    def test_restock_query(self, mock_review_system):
        """Test restock queries"""
        mock_review_system.requires_human_review.return_value = False
        
        response = chatbot_agent.chatbot_response("When will product A101 be restocked?")
        assert "A101" in response
        assert "10" in response  # Quantity
        
        # Test non-existent product
        response = chatbot_agent.chatbot_response("When will product X999 be restocked?")
        assert "No restock" in response or "not found" in response
    
    @patch('chatbot_agent.review_system')
    def test_complex_query_escalation(self, mock_review_system):
        """Test escalation of complex queries"""
        mock_review_system.requires_human_review.return_value = True
        mock_review_system.submit_for_review.return_value = "test_review_id"
        
        response = chatbot_agent.chatbot_response("This is urgent! My order is missing!")
        assert "forwarded to our support team" in response
        assert "test_review_id" in response
    
    @patch('chatbot_agent.review_system')
    def test_default_response(self, mock_review_system):
        """Test default response for unrecognized queries"""
        mock_review_system.requires_human_review.return_value = False
        
        response = chatbot_agent.chatbot_response("Hello there")
        assert "I can help with" in response
        assert "order" in response.lower()
        assert "restock" in response.lower()

class TestHumanReviewSystem:
    """Test the human review system"""
    
    def setup_method(self):
        """Set up test environment for human review"""
        self.test_dir = tempfile.mkdtemp()
        self.review_system = HumanReviewSystem()
        self.review_system.pending_reviews_file = os.path.join(self.test_dir, 'pending.json')
        self.review_system.review_log_file = os.path.join(self.test_dir, 'log.csv')
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_confidence_calculation_restock(self):
        """Test confidence calculation for restock decisions"""
        # Normal quantity should have high confidence
        data = {"product_id": "A101", "quantity": 5}
        confidence = self.review_system.calculate_confidence("restock", data)
        assert confidence > 0.7
        
        # Very high quantity should have lower confidence
        data = {"product_id": "A101", "quantity": 25}
        confidence = self.review_system.calculate_confidence("restock", data)
        assert confidence < 0.7
        
        # Edge case: zero quantity
        data = {"product_id": "A101", "quantity": 0}
        confidence = self.review_system.calculate_confidence("restock", data)
        assert confidence >= 0.1  # Should not go below minimum
    
    def test_confidence_calculation_chatbot(self):
        """Test confidence calculation for chatbot responses"""
        # Normal query should have high confidence
        data = {"query": "Where is my order?"}
        confidence = self.review_system.calculate_confidence("chatbot_response", data)
        assert confidence > 0.7
        
        # Urgent query should have lower confidence
        data = {"query": "This is urgent! Emergency!"}
        confidence = self.review_system.calculate_confidence("chatbot_response", data)
        assert confidence < 0.7
        
        # Multiple urgent keywords
        data = {"query": "URGENT EMERGENCY COMPLAINT REFUND"}
        confidence = self.review_system.calculate_confidence("chatbot_response", data)
        assert confidence < 0.4
    
    def test_submit_and_approve_review(self):
        """Test submitting and approving a review"""
        data = {"product_id": "A101", "quantity": 25}
        review_id = self.review_system.submit_for_review("restock", data, "Test decision")
        
        # Check pending reviews
        pending = self.review_system.get_pending_reviews()
        assert len(pending) == 1
        assert pending[0]["review_id"] == review_id
        assert pending[0]["status"] == "pending"
        
        # Approve the review
        success = self.review_system.approve_decision(review_id, "Approved for testing")
        assert success
        
        # Check it's no longer pending
        pending = self.review_system.get_pending_reviews()
        assert len(pending) == 0
        
        # Check it's logged
        assert os.path.exists(self.review_system.review_log_file)
    
    def test_submit_and_reject_review(self):
        """Test submitting and rejecting a review"""
        data = {"product_id": "B202", "quantity": 30}
        review_id = self.review_system.submit_for_review("restock", data, "Test decision")
        
        # Reject the review
        success = self.review_system.reject_decision(review_id, "Quantity too high")
        assert success
        
        # Check it's no longer pending
        pending = self.review_system.get_pending_reviews()
        assert len(pending) == 0
    
    def test_invalid_review_id(self):
        """Test handling of invalid review IDs"""
        success = self.review_system.approve_decision("invalid_id", "Test")
        assert not success
        
        success = self.review_system.reject_decision("invalid_id", "Test")
        assert not success

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=../", "--cov-report=html"])
