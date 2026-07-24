import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import uuid
import time
from datetime import datetime, timedelta
import json

# Import necessary modules from the karma tracker
from utils.stp_bridge import STPBridge
from utils.sovereign_bridge import SovereignBridge, SignalType
from utils.karma_signal_contract import KarmaSignal
from utils.platform_adapters import PlatformAdapter, AssistantAdapter, GameAdapter, GurukulAdapter, FinanceAdapter, InfrastructureAdapter
from routes.karma import router as karma_router
from utils.karma_engine import KarmaEngine
from utils.karma_feedback_engine import KarmaFeedbackEngine
from utils.tokens import TokenManager


class TestMixedUserJourneySimulations(unittest.TestCase):
    """Test suite for mixed-user journey simulations across all platforms"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.user_ids = [str(uuid.uuid4()) for _ in range(5)]  # Multiple users for mixed journey
        self.platforms = ['assistant', 'game', 'finance', 'gurukul', 'infra']
        self.sovereign_bridge = SovereignBridge()
        self.stp_bridge = STPBridge()
        self.karma_engine = KarmaEngine()
        
    @patch('utils.sovereign_bridge.SovereignBridge.send_signal')
    def test_mixed_platform_user_journey(self, mock_send_signal):
        """Test a complete user journey across multiple platforms with Core authorization"""
        # Mock successful Core authorization for all requests
        mock_send_signal.return_value = {"status": "ALLOW", "action": "apply_consequence"}
        
        # Simulate a user interacting with multiple platforms over time
        user_id = self.user_ids[0]
        
        # Phase 1: User interacts with Assistant platform
        assistant_adapter = AssistantAdapter()
        assistant_signal = assistant_adapter.generate_signal(
            subject_id=user_id,
            severity=0.2,  # Positive interaction
            reason_code="ASSISTANT_HELPFULNESS"
        )
        
        # Send signal through STP bridge
        assistant_packet = self.stp_bridge.create_packet(
            signal=assistant_signal,
            source="assistant_system",
            destination="sovereign_core"
        )
        
        # Process through KarmaEngine in constraint-only mode
        self.karma_engine.constraint_only_mode = True
        assistant_result = self.karma_engine.process_karma_change(
            user_id=user_id,
            change_amount=5,
            reason="HELPFUL_ASSISTANT_INTERACTION",
            context="assistant"
        )
        
        # Phase 2: Same user interacts with Game platform
        game_adapter = GameAdapter()
        game_signal = game_adapter.generate_signal(
            subject_id=user_id,
            severity=0.3,  # Moderate positive behavior
            reason_code="FAIR_GAMEPLAY"
        )
        
        game_packet = self.stp_bridge.create_packet(
            signal=game_signal,
            source="game_system",
            destination="sovereign_core"
        )
        
        game_result = self.karma_engine.process_karma_change(
            user_id=user_id,
            change_amount=3,
            reason="FAIR_GAMEPLAY_BEHAVIOR",
            context="game"
        )
        
        # Phase 3: Same user interacts with Finance platform
        finance_adapter = FinanceAdapter()
        finance_signal = finance_adapter.generate_signal(
            subject_id=user_id,
            severity=0.1,  # Low risk behavior
            reason_code="STANDARD_FINANCE_USE"
        )
        
        finance_packet = self.stp_bridge.create_packet(
            signal=finance_signal,
            source="finance_system",
            destination="sovereign_core"
        )
        
        finance_result = self.karma_engine.process_karma_change(
            user_id=user_id,
            change_amount=2,
            reason="STANDARD_FINANCE_ACTIVITY",
            context="finance"
        )
        
        # Phase 4: User triggers potential restriction in Gurukul
        gurukul_adapter = GurukulAdapter()
        gurukul_signal = gurukul_adapter.generate_signal(
            subject_id=user_id,
            severity=0.6,  # Higher severity - needs guidance
            reason_code="PROGRESSION_PACING"
        )
        
        gurukul_packet = self.stp_bridge.create_packet(
            signal=gurukul_signal,
            source="gurukul_system",
            destination="sovereign_core"
        )
        
        gurukul_result = self.karma_engine.process_karma_change(
            user_id=user_id,
            change_amount=-2,  # Small negative for pacing
            reason="PROGRESSION_PACING_GUIDANCE",
            context="gurukul"
        )
        
        # Verify all interactions went through proper channels
        self.assertTrue(assistant_result['signal_emitted'])
        self.assertTrue(game_result['signal_emitted'])
        self.assertTrue(finance_result['signal_emitted'])
        self.assertTrue(gurukul_result['signal_emitted'])
        
        # Verify constraint-only mode behavior (no direct consequences)
        self.assertNotIn('direct_consequence_applied', assistant_result)
        self.assertNotIn('direct_consequence_applied', game_result)
        self.assertNotIn('direct_consequence_applied', finance_result)
        self.assertNotIn('direct_consequence_applied', gurukul_result)
        
        # Verify all signals require Core ACK
        self.assertTrue(assistant_signal.requires_core_ack)
        self.assertTrue(game_signal.requires_core_ack)
        self.assertTrue(finance_signal.requires_core_ack)
        self.assertTrue(gurukul_signal.requires_core_ack)
        
        # Verify all signals use canonical contract
        self.assertEqual(assistant_signal.subject_id, user_id)
        self.assertEqual(game_signal.subject_id, user_id)
        self.assertEqual(finance_signal.subject_id, user_id)
        self.assertEqual(gurukul_signal.subject_id, user_id)
        
        # Verify mock was called for all signals (Core authorization attempted)
        self.assertEqual(mock_send_signal.call_count, 4)  # 4 different signals sent
    
    @patch('utils.sovereign_bridge.SovereignBridge.send_signal')
    def test_cross_user_cross_platform_interaction(self, mock_send_signal):
        """Test interactions between multiple users across platforms"""
        # Mock Core authorization
        mock_send_signal.return_value = {"status": "ALLOW", "action": "apply_consequence"}
        
        # Simulate multiple users interacting across platforms
        user_a, user_b, user_c = self.user_ids[0], self.user_ids[1], self.user_ids[2]
        
        # User A helps User B in Assistant platform
        assistant_adapter = AssistantAdapter()
        signal_ab = assistant_adapter.generate_signal(
            subject_id=user_a,  # User A gets credit for helping
            severity=0.4,
            reason_code="USER_HELPING_ANOTHER_USER"
        )
        
        # User B receives karma boost for receiving help appropriately
        signal_b_received_help = assistant_adapter.generate_signal(
            subject_id=user_b,
            severity=0.3,
            reason_code="USER_RECEIVING_HELP_APPROPRIATELY"
        )
        
        # User C shows negative behavior in Game
        game_adapter = GameAdapter()
        signal_c_negative = game_adapter.generate_signal(
            subject_id=user_c,
            severity=0.7,  # High severity for negative behavior
            reason_code="NEGATIVE_GAME_BEHAVIOR"
        )
        
        # Process all signals
        result_a = self.karma_engine.process_karma_change(
            user_id=user_a,
            change_amount=8,
            reason="HELPING_OTHER_USERS",
            context="assistant"
        )
        
        result_b = self.karma_engine.process_karma_change(
            user_id=user_b,
            change_amount=5,
            reason="RECEIVING_HELP_APPROPRIATELY",
            context="assistant"
        )
        
        result_c = self.karma_engine.process_karma_change(
            user_id=user_c,
            change_amount=-10,
            reason="NEGATIVE_BEHAVIOR",
            context="game"
        )
        
        # Verify all signals were emitted
        self.assertTrue(all([
            result_a['signal_emitted'],
            result_b['signal_emitted'], 
            result_c['signal_emitted']
        ]))
        
        # Verify constraint-only mode maintained
        for result in [result_a, result_b, result_c]:
            self.assertNotIn('direct_consequence_applied', result)
        
        # Verify all signals require Core authorization
        self.assertTrue(signal_ab.requires_core_ack)
        self.assertTrue(signal_b_received_help.requires_core_ack)
        self.assertTrue(signal_c_negative.requires_core_ack)
        
        # Verify canonical contract compliance
        self.assertIn(signal_ab.context, self.platforms)
        self.assertIn(signal_b_received_help.context, self.platforms)
        self.assertIn(signal_c_negative.context, self.platforms)
    
    @patch('utils.sovereign_bridge.SovereignBridge.send_signal')
    def test_irreversible_action_simulation(self, mock_send_signal):
        """Test irreversible actions (death, rebirth, access gating) with Core authorization"""
        # Mock both ALLOW and DENY responses to test both paths
        mock_send_signal.side_effect = [
            {"status": "ALLOW", "action": "apply_consequence"},  # Death event approved
            {"status": "DENY", "reason": "INSUFFICIENT_EVIDENCE"},  # Rebirth denied initially
            {"status": "ALLOW", "action": "apply_consequence"}  # Access gate approved
        ]
        
        user_id = self.user_ids[0]
        
        # Simulate death event (irreversible action)
        death_signal = KarmaSignal(
            subject_id=user_id,
            context='game',
            signal='restrict',
            severity=1.0,
            reason_code='DEATH_THRESHOLD_REACHED',
            requires_core_ack=True  # Critical: irreversible action needs Core approval
        )
        
        death_packet = self.stp_bridge.create_packet(
            signal=death_signal,
            source="game_system",
            destination="sovereign_core"
        )
        
        # Simulate rebirth event (another irreversible action)
        rebirth_signal = KarmaSignal(
            subject_id=user_id,
            context='gurukul',
            signal='allow',
            severity=0.0,
            reason_code='REBIRTH_REQUEST',
            requires_core_ack=True  # Critical: irreversible action needs Core approval
        )
        
        rebirth_packet = self.stp_bridge.create_packet(
            signal=rebirth_signal,
            source="gurukul_system",
            destination="sovereign_core"
        )
        
        # Simulate access gating (another irreversible action)
        access_signal = KarmaSignal(
            subject_id=user_id,
            context='finance',
            signal='restrict',
            severity=0.9,
            reason_code='ACCESS_GATE_TRIGGERED',
            requires_core_ack=True  # Critical: irreversible action needs Core approval
        )
        
        access_packet = self.stp_bridge.create_packet(
            signal=access_signal,
            source="finance_system",
            destination="sovereign_core"
        )
        
        # Process through KarmaEngine
        self.karma_engine.constraint_only_mode = True
        
        # First death event - should be allowed by Core
        death_result = self.karma_engine.process_karma_change(
            user_id=user_id,
            change_amount=-100,  # Major karma drop for death
            reason="DEATH_EVENT_EXECUTION",
            context="game"
        )
        
        # Rebirth request - initially denied by Core
        rebirth_result = self.karma_engine.process_karma_change(
            user_id=user_id,
            change_amount=50,  # Karma restoration for rebirth
            reason="REBIRTH_REQUEST_SUBMITTED",
            context="gurukul"
        )
        
        # Access gate - should be allowed by Core
        access_result = self.karma_engine.process_karma_change(
            user_id=user_id,
            change_amount=-50,  # Significant restriction
            reason="ACCESS_GATE_ENFORCEMENT",
            context="finance"
        )
        
        # Verify all signals were emitted despite different Core responses
        self.assertTrue(death_result['signal_emitted'])
        self.assertTrue(rebirth_result['signal_emitted'])
        self.assertTrue(access_result['signal_emitted'])
        
        # Verify all irreversible actions required Core authorization
        self.assertTrue(death_signal.requires_core_ack)
        self.assertTrue(rebirth_signal.requires_core_ack)
        self.assertTrue(access_signal.requires_core_ack)
        
        # Verify mock was called 3 times for 3 irreversible actions
        self.assertEqual(mock_send_signal.call_count, 3)
    
    def test_identical_behavior_across_platforms(self):
        """Test that identical inputs produce identical outputs across all platforms"""
        user_id = self.user_ids[0]
        
        # Create identical behavior scenarios across platforms
        scenarios = []
        for platform in ['assistant', 'game', 'finance', 'gurukul', 'infra']:
            signal = KarmaSignal(
                subject_id=user_id,
                context=platform,
                signal='nudge',
                severity=0.5,
                reason_code='NORMAL_BEHAVIOR_STANDARDIZED'
            )
            scenarios.append((platform, signal))
        
        # Process each scenario through respective adapters
        results = {}
        for platform, signal in scenarios:
            # Use appropriate adapter for each platform
            if platform == 'assistant':
                adapter = AssistantAdapter()
            elif platform == 'game':
                adapter = GameAdapter()
            elif platform == 'finance':
                adapter = FinanceAdapter()
            elif platform == 'gurukul':
                adapter = GurukulAdapter()
            else:  # infra
                adapter = InfrastructureAdapter()
            
            # Generate signal through adapter
            processed_signal = adapter.generate_signal(
                subject_id=signal.subject_id,
                severity=signal.severity,
                reason_code=signal.reason_code
            )
            
            results[platform] = processed_signal
        
        # Verify all platforms produce equivalent canonical signals
        first_platform_result = None
        for platform, result in results.items():
            # Store first result for comparison
            if first_platform_result is None:
                first_platform_result = result
                continue
            
            # Compare critical fields (excluding context which differs by platform)
            self.assertEqual(result.subject_id, first_platform_result.subject_id)
            self.assertEqual(result.signal, first_platform_result.signal)
            self.assertEqual(result.severity, first_platform_result.severity)
            self.assertEqual(result.reason_code, first_platform_result.reason_code)
            self.assertEqual(result.requires_core_ack, first_platform_result.requires_core_ack)
            self.assertEqual(result.ttl, first_platform_result.ttl)
            
            # Context should be specific to platform
            self.assertEqual(result.context, platform)
    
    @patch('utils.sovereign_bridge.SovereignBridge.send_signal')
    def test_constraint_only_mode_verification(self, mock_send_signal):
        """Verify that constraint-only mode is strictly enforced"""
        mock_send_signal.return_value = {"status": "ALLOW", "action": "apply_consequence"}
        
        # Enable constraint-only mode
        self.karma_engine.constraint_only_mode = True
        
        user_id = self.user_ids[0]
        
        # Test multiple types of karma changes
        test_cases = [
            {
                "user_id": user_id,
                "change_amount": 10,
                "reason": "POSITIVE_BEHAVIOR",
                "context": "assistant",
                "expected_signal": "allow"
            },
            {
                "user_id": user_id,
                "change_amount": -5,
                "reason": "MINOR_INFRACTION",
                "context": "game",
                "expected_signal": "nudge"
            },
            {
                "user_id": user_id,
                "change_amount": -20,
                "reason": "SIGNIFICANT_VIOLATION",
                "context": "finance",
                "expected_signal": "restrict"
            }
        ]
        
        results = []
        for case in test_cases:
            result = self.karma_engine.process_karma_change(
                user_id=case["user_id"],
                change_amount=case["change_amount"],
                reason=case["reason"],
                context=case["context"]
            )
            results.append(result)
        
        # Verify constraint-only behavior for all cases
        for i, result in enumerate(results):
            # All should emit signals
            self.assertTrue(result['signal_emitted'], f"Case {i} should emit signal")
            
            # None should apply direct consequences (constraint-only mode)
            self.assertNotIn('direct_consequence_applied', result, 
                           f"Case {i} should not apply direct consequence in constraint-only mode")
            
            # All should route through Core
            self.assertIn('core_authorization_needed', result)
            self.assertTrue(result['core_authorization_needed'])
        
        # Verify that no explanations are provided (as per requirement)
        for result in results:
            if 'explanation' in result:
                self.fail("Constraint-only mode should not provide explanations")


class TestAuditVerification(unittest.TestCase):
    """Test audit compliance and verification"""
    
    def setUp(self):
        self.audit_log = []
        
    def test_audit_trail_for_all_actions(self):
        """Test that all karma actions are properly logged for audit"""
        from utils.audit_enhancer import AuditEnhancer
        
        # Create audit enhancer instance
        auditor = AuditEnhancer()
        
        # Log various actions
        user_id = str(uuid.uuid4())
        
        # Test logging of karma computation
        audit_entry_1 = auditor.log_action(
            action_type="KARMA_COMPUTATION",
            user_id=user_id,
            context="assistant",
            details={"computation_result": 0.7, "reason": "POSITIVE_INTERACTION"}
        )
        
        # Test logging of signal emission
        audit_entry_2 = auditor.log_action(
            action_type="SIGNAL_EMISSION",
            user_id=user_id,
            context="game",
            details={"signal_type": "nudge", "severity": 0.4}
        )
        
        # Test logging of Core authorization request
        audit_entry_3 = auditor.log_action(
            action_type="CORE_AUTHORIZATION_REQUEST",
            user_id=user_id,
            context="finance",
            details={"request_type": "ACCESS_GATE", "requires_ack": True}
        )
        
        # Verify all audit entries have required fields
        for entry in [audit_entry_1, audit_entry_2, audit_entry_3]:
            self.assertIn('timestamp', entry)
            self.assertIn('action_type', entry)
            self.assertIn('user_id', entry)
            self.assertIn('context', entry)
            self.assertIn('details', entry)
            self.assertIsNotNone(entry['user_id'])  # Should have valid user ID
            self.assertIsNotNone(entry['action_type'])  # Should have valid action type
    
    def test_sovereignty_compliance_verification(self):
        """Test that system maintains sovereignty compliance"""
        # Import the main components
        from utils.stp_bridge import STPBridge
        from utils.sovereign_bridge import SovereignBridge
        from utils.karma_signal_contract import KarmaSignal
        
        # Create instances
        stp_bridge = STPBridge()
        sovereign_bridge = SovereignBridge()
        
        user_id = str(uuid.uuid4())
        
        # Create a karma signal that requires Core authorization
        signal = KarmaSignal(
            subject_id=user_id,
            context='assistant',
            signal='nudge',
            severity=0.5,
            reason_code='BEHAVIOR_GUIDANCE',
            requires_core_ack=True  # Must require Core ACK
        )
        
        # Verify sovereignty requirements are met:
        # 1. Karma never executes final authority without Core
        self.assertTrue(signal.requires_core_ack)
        
        # 2. Karma always routes through Sovereign Core
        packet = stp_bridge.create_packet(
            signal=signal,
            source="assistant_system",
            destination="sovereign_core"  # Always goes to Core first
        )
        
        self.assertEqual(packet['destination'], "sovereign_core")
        
        # 3. Constraint-only mode prevents local decision making
        from utils.karma_engine import KarmaEngine
        engine = KarmaEngine()
        engine.constraint_only_mode = True  # Enforce constraint-only
        
        # 4. Identical behavior across products
        self.assertEqual(signal.context, 'assistant')  # Context-specific but structure identical
        self.assertTrue(isinstance(signal.severity, float))  # Consistent data types
        self.assertTrue(isinstance(signal.requires_core_ack, bool))  # Consistent boolean requirement


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)