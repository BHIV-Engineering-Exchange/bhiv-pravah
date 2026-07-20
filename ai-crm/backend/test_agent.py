#!/usr/bin/env python3
"""
Test Suite for AI Agent Logistics System
Run with: python test_agent.py
"""

import unittest
import pandas as pd
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import modules to test
import agent
import chatbot_agent
from human_review import HumanReviewSystem

class TestAgentLogic(unittest.TestCase):
    """Test the main agent logic"""
    
    def setUp(self):
        """Set up test environment"""
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
    
    def tearDown(self):
        """Clean up test environment"""
        # Restore original file paths
        for key, value in self.original_files.items():
            setattr(agent, key, value)
        
        # Clean up test directory
        shutil.rmtree(self.test_dir)
    
    def test_sense_function(self):
        """Test the sense function reads data correctly"""
        result = agent.sense()
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 4)
        self.assertIn('ProductID', result.columns)
        self.assertIn('ReturnQuantity', result.columns)
    
    def test_plan_function(self):
        """Test the plan function identifies correct restocks"""
        df = self.test_returns_data
        result = agent.plan(df)
        
        # Should identify A101 (6) and C303 (15) as needing restock (>5)
        self.assertEqual(len(result), 2)
        
        product_ids = [item['ProductID'] for item in result]
        self.assertIn('A101', product_ids)
        self.assertIn('C303', product_ids)
        self.assertNotIn('B202', product_ids)  # Only 3 returns
        self.assertNotIn('D404', product_ids)  # Only 2 returns
    
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
        self.assertTrue(os.path.exists(agent.RESTOCK_FILE))
        
        # Check if log file was created
        self.assertTrue(os.path.exists(agent.LOG_FILE))
        
        # Verify restock data
        restock_df = pd.read_excel(agent.RESTOCK_FILE)
        self.assertEqual(len(restock_df), 2)
    
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
        self.assertFalse(os.path.exists(agent.RESTOCK_FILE))
        
        # Should submit for review
        mock_review_system.submit_for_review.assert_called_once()

class TestChatbotLogic(unittest.TestCase):
    """Test the chatbot logic"""
    
    def setUp(self):
        """Set up test data for chatbot"""
        # Create test data files
        self.test_dir = tempfile.mkdtemp()
        
        orders_data = pd.DataFrame({
            'OrderID': [101, 102, 103],
            'Status': ['Shipped', 'Delivered', 'Processing']
        })
        
        restocks_data = pd.DataFrame({
            'ProductID': ['A101', 'B202'],
            'RestockQuantity': [10, 5]
        })
        
        self.orders_file = os.path.join(self.test_dir, 'orders.xlsx')
        self.restocks_file = os.path.join(self.test_dir, 'restocks.xlsx')
        
        orders_data.to_excel(self.orders_file, index=False)
        restocks_data.to_excel(self.restocks_file, index=False)
        
        # Patch the file paths in chatbot_agent
        chatbot_agent.orders_df = orders_data
        chatbot_agent.restocks_df = restocks_data
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_extract_order_id(self):
        """Test order ID extraction from messages"""
        self.assertEqual(chatbot_agent.extract_order_id("Where is my order #123?"), 123)
        self.assertEqual(chatbot_agent.extract_order_id("order 456"), 456)
        self.assertEqual(chatbot_agent.extract_order_id("no order here"), None)
    
    def test_extract_product_id(self):
        """Test product ID extraction from messages"""
        self.assertEqual(chatbot_agent.extract_product_id("When will product A101 be restocked?"), "A101")
        self.assertEqual(chatbot_agent.extract_product_id("Product b202 status"), "B202")
        self.assertEqual(chatbot_agent.extract_product_id("no product here"), None)
    
    @patch('chatbot_agent.review_system')
    def test_order_status_query(self, mock_review_system):
        """Test order status queries"""
        mock_review_system.requires_human_review.return_value = False
        
        response = chatbot_agent.chatbot_response("Where is my order #101?")
        self.assertIn("Shipped", response)
        self.assertIn("#101", response)
    
    @patch('chatbot_agent.review_system')
    def test_restock_query(self, mock_review_system):
        """Test restock queries"""
        mock_review_system.requires_human_review.return_value = False
        
        response = chatbot_agent.chatbot_response("When will product A101 be restocked?")
        self.assertIn("A101", response)
        self.assertIn("10", response)  # Quantity
    
    @patch('chatbot_agent.review_system')
    def test_complex_query_escalation(self, mock_review_system):
        """Test escalation of complex queries"""
        mock_review_system.requires_human_review.return_value = True
        mock_review_system.submit_for_review.return_value = "test_review_id"
        
        response = chatbot_agent.chatbot_response("This is urgent! My order is missing!")
        self.assertIn("forwarded to our support team", response)
        self.assertIn("test_review_id", response)

class TestHumanReviewSystem(unittest.TestCase):
    """Test the human review system"""
    
    def setUp(self):
        """Set up test environment for human review"""
        self.test_dir = tempfile.mkdtemp()
        self.review_system = HumanReviewSystem()
        self.review_system.pending_reviews_file = os.path.join(self.test_dir, 'pending.json')
        self.review_system.review_log_file = os.path.join(self.test_dir, 'log.csv')
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_confidence_calculation_restock(self):
        """Test confidence calculation for restock decisions"""
        # Normal quantity should have high confidence
        data = {"product_id": "A101", "quantity": 5}
        confidence = self.review_system.calculate_confidence("restock", data)
        self.assertGreater(confidence, 0.7)
        
        # Very high quantity should have lower confidence
        data = {"product_id": "A101", "quantity": 25}
        confidence = self.review_system.calculate_confidence("restock", data)
        self.assertLess(confidence, 0.7)
    
    def test_confidence_calculation_chatbot(self):
        """Test confidence calculation for chatbot responses"""
        # Normal query should have high confidence
        data = {"query": "Where is my order?"}
        confidence = self.review_system.calculate_confidence("chatbot_response", data)
        self.assertGreater(confidence, 0.7)
        
        # Urgent query should have lower confidence
        data = {"query": "This is urgent! Emergency!"}
        confidence = self.review_system.calculate_confidence("chatbot_response", data)
        self.assertLess(confidence, 0.7)
    
    def test_submit_and_approve_review(self):
        """Test submitting and approving a review"""
        data = {"product_id": "A101", "quantity": 25}
        review_id = self.review_system.submit_for_review("restock", data, "Test decision")
        
        # Check pending reviews
        pending = self.review_system.get_pending_reviews()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["review_id"], review_id)
        
        # Approve the review
        success = self.review_system.approve_decision(review_id, "Approved for testing")
        self.assertTrue(success)
        
        # Check it's no longer pending
        pending = self.review_system.get_pending_reviews()
        self.assertEqual(len(pending), 0)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test data
        returns_data = pd.DataFrame({
            'ProductID': ['A101', 'B202', 'C303'],
            'ReturnQuantity': [6, 3, 25]  # Mix of high and low confidence
        })
        
        self.returns_file = os.path.join(self.test_dir, 'returns.xlsx')
        returns_data.to_excel(self.returns_file, index=False)
        
        # Patch agent file paths
        agent.RETURNS_FILE = self.returns_file
        agent.RESTOCK_FILE = os.path.join(self.test_dir, 'restock.xlsx')
        agent.LOG_FILE = os.path.join(self.test_dir, 'logs.csv')
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.test_dir)
    
    @patch('agent.review_system')
    def test_end_to_end_workflow(self, mock_review_system):
        """Test complete agent workflow"""
        # Mock review system to auto-approve normal quantities
        def mock_requires_review(action_type, data):
            return data.get("quantity", 0) > 20
        
        mock_review_system.requires_human_review.side_effect = mock_requires_review
        mock_review_system.submit_for_review.return_value = "test_review_id"
        
        # Run the agent
        agent.run_agent()
        
        # Check results
        # Should have created restock file with A101 (auto-approved)
        # C303 should be submitted for review (quantity 25)
        if os.path.exists(agent.RESTOCK_FILE):
            restock_df = pd.read_excel(agent.RESTOCK_FILE)
            # Should contain A101 but not C303
            product_ids = restock_df['ProductID'].tolist()
            self.assertIn('A101', product_ids)
            self.assertNotIn('C303', product_ids)

def run_performance_tests():
    """Run performance tests and generate report"""
    print("\n🚀 Running Performance Tests...")
    
    import time
    
    # Test agent processing speed
    start_time = time.time()
    agent.run_agent()
    agent_time = time.time() - start_time
    
    print(f"⏱️  Agent processing time: {agent_time:.3f} seconds")
    
    # Test chatbot response time
    start_time = time.time()
    response = chatbot_agent.chatbot_response("Where is my order #101?")
    chatbot_time = time.time() - start_time
    
    print(f"⏱️  Chatbot response time: {chatbot_time:.3f} seconds")
    print(f"📝 Chatbot response: {response}")
    
    # Performance targets
    print("\n📊 Performance Analysis:")
    print(f"Agent Speed: {'✅ PASS' if agent_time < 5.0 else '❌ FAIL'} (Target: <5s)")
    print(f"Chatbot Speed: {'✅ PASS' if chatbot_time < 0.5 else '❌ FAIL'} (Target: <0.5s)")

if __name__ == "__main__":
    print("🧪 AI Agent Test Suite")
    print("=" * 50)
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance tests
    run_performance_tests()
    
    print("\n✅ Test suite completed!")
