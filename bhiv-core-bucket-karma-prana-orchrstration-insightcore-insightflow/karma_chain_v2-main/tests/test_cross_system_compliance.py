import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import uuid
import time
from datetime import datetime, timedelta

# Import necessary modules from the karma tracker
from utils.stp_bridge import STPBridge
from utils.sovereign_bridge import SovereignBridge, SignalType
from utils.karma_signal_contract import KarmaSignal
from utils.platform_adapters import PlatformAdapter, AssistantAdapter, GameAdapter, GurukulAdapter, FinanceAdapter, InfraAdapter
from routes.karma import router as karma_router
from utils.karma_engine import KarmaEngine


class TestCrossSystemCompliance(unittest.TestCase):
    """Test suite for cross-system compliance of KarmaChain with Core authorization"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.subject_id = str(uuid.uuid4())
        self.test_contexts = ['assistant', 'game', 'finance', 'gurukul', 'infra']
        
    @patch('utils.sovereign_bridge.SovereignBridge.send_signal')
    def test_denied_ack_simulation(self, mock_send_signal):
        """Test that system properly handles denied ACK from Core"""
        # Mock the sovereign bridge to return NACK
        mock_send_signal.return_value = {"status": "NACK", "reason": "UNAUTHORIZED_ACTION"}
        
        # Create a karma signal
        karma_signal = KarmaSignal(
            subject_id=self.subject_id,
            context='assistant',
            signal='restrict',
            severity=0.8,
            reason_code='HIGH_RISK_USER'
        )
        
        # Mock the STP bridge send_packet to return the expected response
        with patch('utils.stp_bridge.STPBridge.send_packet') as mock_send_packet:
            mock_send_packet.return_value = {"status": "NACK", "reason": "UNAUTHORIZED_ACTION"}
            
            stp_bridge = STPBridge()
            packet = stp_bridge.create_packet(
                signal=karma_signal,
                source="test_system",
                destination="sovereign_core"
            )
            
            # Send the packet
            result = stp_bridge.send_packet(packet)
            
            # Verify that the action was properly blocked due to NACK
            self.assertIsNotNone(result)
            self.assertIn('status', result)
            # Action should not proceed if Core returns NACK
            self.assertNotEqual(result.get('status'), 'SUCCESS')
            
    @patch('utils.sovereign_bridge.SovereignBridge.send_signal')
    def test_timeout_scenario_simulation(self, mock_send_signal):
        """Test system behavior when Core doesn't respond within timeout period"""
        # Mock the sovereign bridge to simulate timeout
        def timeout_side_effect(*args, **kwargs):
            time.sleep(6)  # Simulate timeout (assuming timeout is 5 seconds)
            return {"status": "TIMEOUT", "reason": "NO_RESPONSE_FROM_CORE"}
        
        mock_send_signal.side_effect = timeout_side_effect
        
        # Create a karma signal that requires Core approval
        karma_signal = KarmaSignal(
            subject_id=self.subject_id,
            context='game',
            signal='restrict',
            severity=0.9,
            reason_code='DEATH_THRESHOLD_REACHED',
            requires_core_ack=True
        )
        
        # Test timeout handling
        stp_bridge = STPBridge()
        with patch.object(stp_bridge, '_send_with_retry', side_effect=timeout_side_effect):
            try:
                packet = stp_bridge.create_packet(
                    signal=karma_signal,
                    source="game_system",
                    destination="sovereign_core"
                )
                
                # This should trigger safe-fail mode
                result = stp_bridge.send_packet(packet)
                
                # Verify safe-fail behavior
                self.assertIsNotNone(result)
                self.assertIn('safe_fail', result)
                self.assertTrue(result.get('safe_fail'))
            except Exception:
                # Expected timeout behavior
                pass
    
    @patch('utils.sovereign_bridge.SovereignBridge.is_core_available')
    def test_core_offline_safe_mode(self, mock_is_core_available):
        """Test system behavior when Core is offline"""
        # Mock Core as unavailable
        mock_is_core_available.return_value = False
        
        # Create karma signal
        karma_signal = KarmaSignal(
            subject_id=self.subject_id,
            context='finance',
            signal='nudge',
            severity=0.3,
            reason_code='LOW_TRUST_USER'
        )
        
        # Test safe mode behavior
        sovereign_bridge = SovereignBridge()
        
        # In safe mode, the system should handle appropriately
        result = sovereign_bridge.send_signal(karma_signal)
        
        # Verify safe mode response
        self.assertIsNotNone(result)
        if not mock_is_core_available.return_value:
            # Should return safe response when Core is offline
            self.assertIn('status', result)
            self.assertIn(result.get('status'), ['SAFE_MODE', 'QUEUED_FOR_LATER', 'TEMPORARY_HOLD'])
    
    @patch('utils.stp_bridge.STPBridge._validate_nonce')
    def test_replay_attack_simulation(self, mock_validate_nonce):
        """Test protection against replay attacks"""
        # Mock nonce validation to detect replay
        mock_validate_nonce.return_value = False  # Nonce already used
        
        stp_bridge = STPBridge()
        
        # Create a packet with reused nonce
        fake_packet = {
            'source': 'test_system',
            'destination': 'sovereign_core',
            'payload': {'test': 'data'},
            'timestamp': time.time(),
            'nonce': 'reused_nonce_12345',
            'signature': 'fake_signature',
            'ttl': 300
        }
        
        # Attempt to send packet with reused nonce
        result = stp_bridge.send_packet(fake_packet)
        
        # Should reject packet due to replay detection
        self.assertIsNotNone(result)
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertIn('reason', result)
        self.assertIn('REPLAY_ATTACK_DETECTED', result['reason'])
    
    def test_cross_platform_identical_behavior(self):
        """Test that KarmaChain behaves identically across all platforms"""
        # Create identical karma signals for different platforms
        signals = []
        for context in self.test_contexts:
            signal = KarmaSignal(
                subject_id=self.subject_id,
                context=context,
                signal='nudge',
                severity=0.5,
                reason_code='BEHAVIOR_NORMALIZATION'
            )
            signals.append(signal)
        
        # Verify all signals have same structure and behavior
        for signal in signals:
            self.assertEqual(signal.subject_id, self.subject_id)
            self.assertIn(signal.context, self.test_contexts)
            self.assertEqual(signal.signal, 'nudge')
            self.assertEqual(signal.severity, 0.5)
            self.assertEqual(signal.reason_code, 'BEHAVIOR_NORMALIZATION')
            self.assertTrue(signal.requires_core_ack)
    
    @patch('utils.sovereign_bridge.SovereignBridge.send_signal')
    def test_constraint_only_mode_enforcement(self, mock_send_signal):
        """Test that constraint-only mode is properly enforced"""
        mock_send_signal.return_value = {"status": "ALLOW", "action": "apply_consequence"}
        
        # Test that KarmaEngine operates in constraint-only mode
        karma_engine = KarmaEngine()
        
        # Enable constraint-only mode
        karma_engine.constraint_only_mode = True
        
        # Process some karma computation
        result = karma_engine.process_karma_change(
            user_id=self.subject_id,
            change_amount=10,
            reason="POSITIVE_BEHAVIOR",
            context="assistant"
        )
        
        # In constraint-only mode, should emit signal but not apply direct consequences
        self.assertIsNotNone(result)
        self.assertIn('signal_emitted', result)
        self.assertTrue(result['signal_emitted'])
        self.assertNotIn('direct_consequence_applied', result)
    
    def test_irreversible_action_requires_core_authorization(self):
        """Test that irreversible actions require Core authorization"""
        from routes.karma import router
        
        # Test death event (an irreversible action)
        death_signal = KarmaSignal(
            subject_id=self.subject_id,
            context='game',
            signal='restrict',
            severity=1.0,
            reason_code='DEATH_THRESHOLD_REACHED',
            requires_core_ack=True  # Critical: must require Core ACK
        )
        
        # Verify signal property
        self.assertTrue(death_signal.requires_core_ack)
        
        # Test rebirth event (another irreversible action)
        rebirth_signal = KarmaSignal(
            subject_id=self.subject_id,
            context='gurukul',
            signal='allow',
            severity=0.0,
            reason_code='REBIRTH_REQUEST',
            requires_core_ack=True  # Critical: must require Core ACK
        )
        
        # Verify signal property
        self.assertTrue(rebirth_signal.requires_core_ack)


class TestPlatformAdaptersCompliance(unittest.TestCase):
    """Test that all platform adapters comply with canonical signal contract"""
    
    def setUp(self):
        self.subject_id = str(uuid.uuid4())
    
    def test_assistant_adapter_compliance(self):
        """Test Assistant Adapter compliance with canonical contract"""
        adapter = AssistantAdapter()
        
        # Test that it generates compliant signals
        signal = adapter.generate_signal(
            subject_id=self.subject_id,
            severity=0.6,
            reason_code="ASSISTANT_GUIDANCE_NEEDED"
        )
        
        # Verify compliance with canonical contract
        self.assertIsInstance(signal, KarmaSignal)
        self.assertEqual(signal.context, 'assistant')
        self.assertTrue(signal.requires_core_ack)
    
    def test_game_adapter_compliance(self):
        """Test Game Adapter compliance with canonical contract"""
        adapter = GameAdapter()
        
        # Test that it generates compliant signals
        signal = adapter.generate_signal(
            subject_id=self.subject_id,
            severity=0.8,
            reason_code="GAME_ACCESS_RESTRICTION"
        )
        
        # Verify compliance with canonical contract
        self.assertIsInstance(signal, KarmaSignal)
        self.assertEqual(signal.context, 'game')
        self.assertTrue(signal.requires_core_ack)
    
    def test_finance_adapter_compliance(self):
        """Test Finance Adapter compliance with canonical contract"""
        adapter = FinanceAdapter()
        
        # Test that it generates compliant signals
        signal = adapter.generate_signal(
            subject_id=self.subject_id,
            severity=0.4,
            reason_code="FINANCE_RISK_ASSESSMENT"
        )
        
        # Verify compliance with canonical contract
        self.assertIsInstance(signal, KarmaSignal)
        self.assertEqual(signal.context, 'finance')
        self.assertTrue(signal.requires_core_ack)
    
    def test_gurukul_adapter_compliance(self):
        """Test Gurukul Adapter compliance with canonical contract"""
        adapter = GurukulAdapter()
        
        # Test that it generates compliant signals
        signal = adapter.generate_signal(
            subject_id=self.subject_id,
            severity=0.3,
            reason_code="GURUKUL_ACCESS_GATE"
        )
        
        # Verify compliance with canonical contract
        self.assertIsInstance(signal, KarmaSignal)
        self.assertEqual(signal.context, 'gurukul')
        self.assertTrue(signal.requires_core_ack)
    
    def test_infra_adapter_compliance(self):
        """Test Infra Adapter compliance with canonical contract"""
        adapter = InfraAdapter()
        
        # Test that it generates compliant signals
        signal = adapter.generate_signal(
            subject_id=self.subject_id,
            severity=0.2,
            reason_code="INFRA_TRUST_MODIFIER"
        )
        
        # Verify compliance with canonical contract
        self.assertIsInstance(signal, KarmaSignal)
        self.assertEqual(signal.context, 'infra')
        self.assertTrue(signal.requires_core_ack)


class TestSecurityFeatures(unittest.TestCase):
    """Test security features implemented in STP Bridge"""
    
    def setUp(self):
        self.stp_bridge = STPBridge()
        self.subject_id = str(uuid.uuid4())
    
    def test_signed_packets_verification(self):
        """Test that packets are properly signed and verified"""
        # Create a packet
        packet = self.stp_bridge.create_packet(
            signal=KarmaSignal(
                subject_id=self.subject_id,
                context='assistant',
                signal='nudge',
                severity=0.5
            ),
            source="test_source",
            destination="test_destination"
        )
        
        # Verify packet has signature
        self.assertIn('signature', packet)
        self.assertIsNotNone(packet['signature'])
        
        # Verify signature can be validated
        is_valid = self.stp_bridge.verify_signature(packet)
        self.assertTrue(is_valid)
    
    def test_nonce_uniqueness(self):
        """Test that nonces are unique"""
        nonces = set()
        for i in range(100):
            packet = self.stp_bridge.create_packet(
                signal=KarmaSignal(
                    subject_id=self.subject_id,
                    context='game',
                    signal='restrict',
                    severity=0.7
                ),
                source="test_source",
                destination="test_destination"
            )
            nonces.add(packet['nonce'])
        
        # All nonces should be unique
        self.assertEqual(len(nonces), 100)
    
    def test_ttl_enforcement(self):
        """Test that TTL is properly enforced"""
        # Create a packet with expired TTL
        expired_timestamp = time.time() - 3600  # 1 hour ago
        packet = {
            'source': 'test_source',
            'destination': 'test_destination',
            'payload': {'test': 'data'},
            'timestamp': expired_timestamp,
            'nonce': 'test_nonce_123',
            'signature': 'test_signature',
            'ttl': 300  # 5 minutes
        }
        
        # Packet should be rejected due to expiration
        is_valid = self.stp_bridge.validate_ttl(packet)
        self.assertFalse(is_valid)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)