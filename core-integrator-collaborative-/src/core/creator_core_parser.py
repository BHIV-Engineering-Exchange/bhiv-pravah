"""
Creator Core Parser
Converts Creator Core blueprint instructions into executable routing decisions
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class RoutingDecision:
    """Routing decision for instruction execution"""
    blueprint_type: str
    target_product: str
    execution_intent: str
    module_path: str
    adapter_name: str
    execution_data: Dict[str, Any]

class CreatorCoreParser:
    """Parses Creator Core blueprint instructions"""
    
    def __init__(self):
        self.product_mappings = {
            'content': 'content_adapter',
            'finance': 'finance_adapter', 
            'workflow': 'workflow_adapter',
            'legal': 'legal_adapter',
            'assistant': 'assistant_adapter',
            'education': 'education_adapter',
            'creator': 'creator_adapter'
        }
    
    def parse_blueprint(self, instruction: Dict[str, Any]) -> RoutingDecision:
        """
        Parse Creator Core instruction into routing decision
        
        Args:
            instruction: Creator Core instruction envelope
            
        Returns:
            RoutingDecision for execution
            
        Raises:
            ValueError: If blueprint cannot be parsed
        """
        payload = instruction.get('payload', {})
        target_product = instruction.get('target_product')
        intent_type = instruction.get('intent_type')
        
        # Extract blueprint type from payload
        blueprint_type = self._extract_blueprint_type(payload)
        
        # Resolve target product adapter
        adapter_name = self._resolve_product_adapter(target_product)
        
        # Determine execution intent
        execution_intent = self._determine_execution_intent(intent_type, blueprint_type)
        
        # Determine module path
        module_path = self._determine_module_path(target_product, blueprint_type)
        
        # Prepare execution data
        execution_data = self._prepare_execution_data(payload, instruction)
        
        return RoutingDecision(
            blueprint_type=blueprint_type,
            target_product=target_product,
            execution_intent=execution_intent,
            module_path=module_path,
            adapter_name=adapter_name,
            execution_data=execution_data
        )
    
    def _extract_blueprint_type(self, payload: Dict[str, Any]) -> str:
        """Extract blueprint type from payload"""
        # Look for blueprint type indicators
        if 'blueprint_type' in payload:
            return payload['blueprint_type']
        
        # Infer from payload structure
        if 'text' in payload or 'content' in payload:
            return 'content_generation'
        elif 'report_type' in payload or 'financial_data' in payload:
            return 'financial_analysis'
        elif 'workflow_steps' in payload or 'process' in payload:
            return 'workflow_execution'
        elif 'legal_document' in payload or 'contract' in payload:
            return 'legal_processing'
        elif 'topic' in payload and 'level' in payload:
            return 'educational_content'
        else:
            return 'general_processing'
    
    def _resolve_product_adapter(self, target_product: str) -> str:
        """Resolve target product to adapter name"""
        if target_product not in self.product_mappings:
            raise ValueError(f"Unknown target product: {target_product}. No fallback allowed.")
        
        return self.product_mappings[target_product]
    
    def _determine_execution_intent(self, intent_type: str, blueprint_type: str) -> str:
        """Determine execution intent from instruction and blueprint"""
        # Map Creator Core intent types to module intents
        intent_mappings = {
            'generate': 'generate',
            'analyze': 'analyze', 
            'process': 'process',
            'create': 'generate',
            'execute': 'process'
        }
        
        return intent_mappings.get(intent_type, 'process')
    
    def _determine_module_path(self, target_product: str, blueprint_type: str) -> str:
        """Determine module path for execution"""
        # Map target product to module name
        module_mappings = {
            'content': 'creator',
            'finance': 'finance',
            'workflow': 'creator', 
            'legal': 'creator',
            'assistant': 'creator',
            'education': 'education',
            'creator': 'creator'
        }
        
        return module_mappings.get(target_product, target_product)
    
    def _prepare_execution_data(self, payload: Dict[str, Any], instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for module execution"""
        # Extract execution data from payload
        execution_data = payload.copy()
        
        # Add instruction metadata
        execution_data['_instruction_metadata'] = {
            'instruction_id': instruction.get('instruction_id'),
            'origin': instruction.get('origin'),
            'timestamp': instruction.get('timestamp'),
            'schema_version': instruction.get('schema_version')
        }
        
        return execution_data