#!/usr/bin/env python3
"""
Integration tests for end-to-end workflows
"""

import pytest
import pandas as pd
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys
sys.path.append('..')

import agent
import chatbot_agent
from human_review import HumanReviewSystem

class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    def setup_method(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        
        # Store original file paths
        self.original_files = {
            'RETURNS_FILE': agent.RETURNS_FILE,
            'RESTOCK_FILE': agent.RESTOCK_FILE,
            'LOG_FILE': agent.LOG_FILE
        }
        
        # Set up test file paths
        agent.RETURNS_FILE = os.path.join(self.test_dir, 'returns.xlsx')
        agent.RESTOCK_FILE = os.path.join(self.test_dir, 'restock.xlsx')
        agent.LOG_FILE = os.path.join(self.test_dir, 'logs.csv')
        
        # Create test data
        self.setup_test_data()
    
    def teardown_method(self):
        """Clean up integration test environment"""
        # Restore original file paths
        for key, value in self.original_files.items():
            setattr(agent, key, value)
        
        # Clean up test directory
        shutil.rmtree(self.test_dir)
    
    def setup_test_data(self):
        """Set up comprehensive test data"""
        # Returns data with mixed scenarios
        returns_data = pd.DataFrame({
            'ProductID': ['A101', 'B202', 'C303', 'D404', 'E505'],
            'ReturnQuantity': [6, 3, 25, 2, 12]  # Mix of high/low confidence
        })
        returns_data.to_excel(agent.RETURNS_FILE, index=False)
        
        # Orders data for chatbot testing
        orders_data = pd.DataFrame({
            'OrderID': [101, 102, 103, 104, 105],
            'Status': ['Shipped', 'Delivered', 'Processing', 'Cancelled', 'In Transit']
        })
        
        # Restock data for chatbot testing
        restocks_data = pd.DataFrame({
            'ProductID': ['A101', 'C303', 'E505'],
            'RestockQuantity': [6, 25, 12]
        })
        
        # Update chatbot data
        chatbot_agent.orders_df = orders_data
        chatbot_agent.restocks_df = restocks_data
    
    @patch('agent.review_system')
    def test_complete_restock_workflow(self, mock_review_system):
        """Test complete workflow: returns → analysis → restock → logging"""
        
        # Configure mock to auto-approve normal quantities, review high quantities
        def mock_requires_review(action_type, data):
            if action_type == "restock":
                return data.get("quantity", 0) > 20
            return False
        
        mock_review_system.requires_human_review.side_effect = mock_requires_review
        mock_review_system.submit_for_review.return_value = "test_review_id"
        
        # Run the complete agent workflow
        agent.run_agent()
        
        # Verify results
        # Should have created restock file with auto-approved items
        assert os.path.exists(agent.RESTOCK_FILE)
        restock_df = pd.read_excel(agent.RESTOCK_FILE)
        
        # Should contain A101 (6) and E505 (12) - auto-approved
        # Should NOT contain C303 (25) - submitted for review
        product_ids = restock_df['ProductID'].tolist()
        assert 'A101' in product_ids
        assert 'E505' in product_ids
        assert 'C303' not in product_ids
        
        # Verify logging
        assert os.path.exists(agent.LOG_FILE)
        logs_df = pd.read_csv(agent.LOG_FILE)
        assert len(logs_df) >= 2  # At least 2 auto-approved actions
        
        # Verify human review was called for high quantity
        mock_review_system.submit_for_review.assert_called()
    
    def test_chatbot_order_tracking_workflow(self):
        """Test complete chatbot workflow for order tracking"""
        
        with patch('chatbot_agent.review_system') as mock_review_system:
            mock_review_system.requires_human_review.return_value = False
            
            # Test various order queries
            test_cases = [
                ("Where is my order #101?", "Shipped"),
                ("What's the status of order 102?", "Delivered"),
                ("Order #103 status please", "Processing"),
                ("Check order 104", "Cancelled"),
                ("Where is order #105?", "In Transit")
            ]
            
            for query, expected_status in test_cases:
                response = chatbot_agent.chatbot_response(query)
                assert expected_status in response
                # Extract order ID more carefully
                order_id = chatbot_agent.extract_order_id(query)
                if order_id:
                    assert str(order_id) in response
    
    def test_chatbot_restock_inquiry_workflow(self):
        """Test complete chatbot workflow for restock inquiries"""
        
        with patch('chatbot_agent.review_system') as mock_review_system:
            mock_review_system.requires_human_review.return_value = False
            
            # Test restock queries
            test_cases = [
                ("When will product A101 be restocked?", "A101", "6"),
                ("Product C303 restock status", "C303", "25"),
                ("Is E505 being restocked?", "E505", "12")
            ]
            
            for query, product_id, quantity in test_cases:
                response = chatbot_agent.chatbot_response(query)
                assert product_id in response
                assert quantity in response
    
    def test_escalation_workflow(self):
        """Test complete escalation workflow"""
        
        with patch('chatbot_agent.review_system') as mock_review_system:
            mock_review_system.requires_human_review.return_value = True
            mock_review_system.submit_for_review.return_value = "escalation_123"
            
            # Test escalation triggers
            urgent_queries = [
                "This is urgent! My order is missing!",
                "EMERGENCY: Need immediate help!",
                "I want to file a complaint about my order",
                "I need a refund right now!"
            ]
            
            for query in urgent_queries:
                response = chatbot_agent.chatbot_response(query)
                assert "forwarded to our support team" in response
                assert "escalation_123" in response
            
            # Verify escalation was called for each query
            assert mock_review_system.submit_for_review.call_count == len(urgent_queries)
    
    def test_human_review_complete_workflow(self):
        """Test complete human review workflow"""
        
        review_system = HumanReviewSystem()
        review_system.pending_reviews_file = os.path.join(self.test_dir, 'pending.json')
        review_system.review_log_file = os.path.join(self.test_dir, 'review_log.csv')
        
        # Submit multiple reviews
        review_ids = []
        
        # High quantity restock (should require review)
        data1 = {"product_id": "X999", "quantity": 50}
        review_id1 = review_system.submit_for_review("restock", data1, "High quantity restock")
        review_ids.append(review_id1)
        
        # Urgent customer query (should require review)
        data2 = {"query": "URGENT: My order is completely wrong!"}
        review_id2 = review_system.submit_for_review("chatbot_response", data2, "Handle urgent query")
        review_ids.append(review_id2)
        
        # Verify both are pending
        pending = review_system.get_pending_reviews()
        assert len(pending) == 2
        
        # Approve first, reject second
        success1 = review_system.approve_decision(review_id1, "Approved after supplier confirmation")
        success2 = review_system.reject_decision(review_id2, "Escalated to senior support")
        
        assert success1
        assert success2
        
        # Verify no pending reviews
        pending = review_system.get_pending_reviews()
        assert len(pending) == 0
        
        # Verify review log exists and has entries
        assert os.path.exists(review_system.review_log_file)
        review_log = pd.read_csv(review_system.review_log_file)
        assert len(review_log) == 2
        
        # Verify decisions are logged correctly
        decisions = review_log['human_decision'].tolist()
        assert 'approved' in decisions
        assert 'rejected' in decisions
    
    def test_data_consistency_workflow(self):
        """Test data consistency across the system"""
        
        with patch('agent.review_system') as mock_review_system:
            mock_review_system.requires_human_review.return_value = False
            
            # Run agent to generate restocks
            agent.run_agent()
            
            # Verify data consistency
            returns_df = pd.read_excel(agent.RETURNS_FILE)
            restock_df = pd.read_excel(agent.RESTOCK_FILE)
            logs_df = pd.read_csv(agent.LOG_FILE)
            
            # Check that all restocked products had sufficient returns
            for _, restock_row in restock_df.iterrows():
                product_id = restock_row['ProductID']
                restock_qty = restock_row['RestockQuantity']
                
                # Find corresponding return
                return_rows = returns_df[returns_df['ProductID'] == product_id]
                assert not return_rows.empty, f"No return data for restocked product {product_id}"
                
                total_returns = return_rows['ReturnQuantity'].sum()
                assert total_returns > agent.THRESHOLD, f"Product {product_id} restocked without sufficient returns"
                
                # Verify restock quantity matches return quantity
                assert restock_qty == total_returns, f"Restock quantity mismatch for {product_id}"
            
            # Check that all restocks are logged
            logged_products = logs_df['ProductID'].tolist()
            for _, restock_row in restock_df.iterrows():
                assert restock_row['ProductID'] in logged_products
    
    def test_error_handling_workflow(self):
        """Test error handling in workflows"""

        # Test with corrupted data
        with patch('agent.sense') as mock_sense:
            mock_sense.side_effect = Exception("File not found")

            # Should handle gracefully and return False
            result = agent.run_agent()
            assert result is False, "Agent should return False on error"
        
        # Test chatbot with invalid data
        with patch('chatbot_agent.orders_df', pd.DataFrame()):
            response = chatbot_agent.chatbot_response("Where is my order #123?")
            assert "couldn't find" in response or "not found" in response
    
    def test_performance_workflow(self):
        """Test performance of complete workflows"""
        import time
        
        with patch('agent.review_system') as mock_review_system:
            mock_review_system.requires_human_review.return_value = False
            
            # Measure agent performance
            start_time = time.time()
            agent.run_agent()
            agent_time = time.time() - start_time
            
            # Should complete within reasonable time
            assert agent_time < 5.0, f"Agent took too long: {agent_time:.2f}s"
            
            # Measure chatbot performance
            start_time = time.time()
            response = chatbot_agent.chatbot_response("Where is my order #101?")
            chatbot_time = time.time() - start_time
            
            # Should respond quickly
            assert chatbot_time < 1.0, f"Chatbot took too long: {chatbot_time:.2f}s"
            assert len(response) > 0, "Chatbot should provide a response"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=../", "--cov-report=html"])
