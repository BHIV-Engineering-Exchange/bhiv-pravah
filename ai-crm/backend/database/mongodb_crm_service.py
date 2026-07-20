#!/usr/bin/env python3
"""
MongoDB CRM Service layer for AI Agent Logistics + CRM System
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import json
import uuid

from .mongodb_connection import get_db, COLLECTIONS
from .mongodb_models import *


class MongoDBCRMService:
    """MongoDB CRM service for managing accounts, contacts, leads, and opportunities"""
    
    def __init__(self):
        self.db = get_db()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # MongoDB doesn't need explicit session cleanup for basic operations
        return False
    
    # === Account Operations ===
    
    def create_account(self, account_data: Dict) -> Dict:
        """Create a new account"""
        try:
            if "account_id" not in account_data or not account_data["account_id"]:
                account_data["account_id"] = f"ACC_{uuid.uuid4().hex[:8].upper()}"
            
            account = AccountModel(**account_data)
            result = self.db[COLLECTIONS['accounts']].insert_one(account.dict(by_alias=True, exclude={"id"}))
            account.id = result.inserted_id
            return self._serialize_doc(account.dict(by_alias=True))
        except Exception as e:
            raise Exception(f"Error creating account: {str(e)}")
    
    def get_accounts(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get accounts with optional filters"""
        query = {}
        if filters:
            if filters.get('account_type'):
                query['account_type'] = filters['account_type']
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('territory'):
                query['territory'] = filters['territory']
            if filters.get('account_manager_id'):
                query['account_manager_id'] = filters['account_manager_id']
        
        accounts = list(self.db[COLLECTIONS['accounts']].find(query).sort("created_at", -1).limit(limit))
        return [self._serialize_doc(account) for account in accounts]
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Get account by ID with full details"""
        account = self.db[COLLECTIONS['accounts']].find_one({"account_id": account_id})
        if account:
            account_dict = self._serialize_doc(account)
            
            # Add related data
            account_dict['contacts'] = self.get_contacts({"account_id": account_id})
            account_dict['opportunities'] = self.get_opportunities({"account_id": account_id})
            account_dict['activities'] = self.get_activities({"account_id": account_id}, limit=10)
            
            return account_dict
        return None
    
    def update_account(self, account_id: str, update_data: Dict) -> bool:
        """Update account"""
        update_data['updated_at'] = datetime.utcnow()
        result = self.db[COLLECTIONS['accounts']].update_one(
            {"account_id": account_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def delete_account(self, account_id: str) -> bool:
        """Delete account (soft delete by setting status to inactive)"""
        return self.update_account(account_id, {"status": "inactive"})
    
    # === Contact Operations ===
    
    def create_contact(self, contact_data: Dict) -> Dict:
        """Create a new contact"""
        try:
            if "contact_id" not in contact_data or not contact_data["contact_id"]:
                contact_data["contact_id"] = f"CON_{uuid.uuid4().hex[:8].upper()}"
            
            contact = ContactModel(**contact_data)
            result = self.db[COLLECTIONS['contacts']].insert_one(contact.dict(by_alias=True, exclude={"id"}))
            contact.id = result.inserted_id
            return self._serialize_doc(contact.dict(by_alias=True))
        except Exception as e:
            raise Exception(f"Error creating contact: {str(e)}")
    
    def get_contacts(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get contacts with optional filters"""
        query = {}
        if filters:
            if filters.get('account_id'):
                query['account_id'] = filters['account_id']
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('contact_role'):
                query['contact_role'] = filters['contact_role']
        
        contacts = list(self.db[COLLECTIONS['contacts']].find(query).sort("created_at", -1).limit(limit))
        return [self._serialize_doc(contact) for contact in contacts]
    
    def get_contact_by_id(self, contact_id: str) -> Optional[Dict]:
        """Get contact by ID"""
        contact = self.db[COLLECTIONS['contacts']].find_one({"contact_id": contact_id})
        return self._serialize_doc(contact) if contact else None
    
    def update_contact(self, contact_id: str, update_data: Dict) -> bool:
        """Update contact"""
        update_data['updated_at'] = datetime.utcnow()
        result = self.db[COLLECTIONS['contacts']].update_one(
            {"contact_id": contact_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # === Lead Operations ===
    
    def create_lead(self, lead_data: Dict) -> Dict:
        """Create a new lead"""
        try:
            if "lead_id" not in lead_data or not lead_data["lead_id"]:
                lead_data["lead_id"] = f"LEAD_{uuid.uuid4().hex[:8].upper()}"
            
            lead = LeadModel(**lead_data)
            result = self.db[COLLECTIONS['leads']].insert_one(lead.dict(by_alias=True, exclude={"id"}))
            lead.id = result.inserted_id
            return self._serialize_doc(lead.dict(by_alias=True))
        except Exception as e:
            raise Exception(f"Error creating lead: {str(e)}")
    
    def get_leads(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get leads with optional filters"""
        query = {}
        if filters:
            if filters.get('lead_status'):
                query['lead_status'] = filters['lead_status']
            if filters.get('assigned_to'):
                query['assigned_to'] = filters['assigned_to']
            if filters.get('converted') is not None:
                query['converted'] = filters['converted']
        
        leads = list(self.db[COLLECTIONS['leads']].find(query).sort("created_at", -1).limit(limit))
        return [self._serialize_doc(lead) for lead in leads]
    
    def get_lead_by_id(self, lead_id: str) -> Optional[Dict]:
        """Get lead by ID"""
        lead = self.db[COLLECTIONS['leads']].find_one({"lead_id": lead_id})
        return self._serialize_doc(lead) if lead else None
    
    def update_lead(self, lead_id: str, update_data: Dict) -> bool:
        """Update lead"""
        update_data['updated_at'] = datetime.utcnow()
        result = self.db[COLLECTIONS['leads']].update_one(
            {"lead_id": lead_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def convert_lead(self, lead_id: str, account_id: str, opportunity_id: str = None) -> bool:
        """Convert a lead to account/opportunity"""
        update_data = {
            "converted": True,
            "converted_at": datetime.utcnow(),
            "converted_to_account_id": account_id,
            "lead_status": "converted",
            "updated_at": datetime.utcnow()
        }
        
        if opportunity_id:
            update_data["converted_to_opportunity_id"] = opportunity_id
        
        result = self.db[COLLECTIONS['leads']].update_one(
            {"lead_id": lead_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # === Opportunity Operations ===
    
    def create_opportunity(self, opp_data: Dict) -> Dict:
        """Create a new opportunity"""
        try:
            if "opportunity_id" not in opp_data or not opp_data["opportunity_id"]:
                opp_data["opportunity_id"] = f"OPP_{uuid.uuid4().hex[:8].upper()}"
            
            opportunity = OpportunityModel(**opp_data)
            result = self.db[COLLECTIONS['opportunities']].insert_one(opportunity.dict(by_alias=True, exclude={"id"}))
            opportunity.id = result.inserted_id
            return self._serialize_doc(opportunity.dict(by_alias=True))
        except Exception as e:
            raise Exception(f"Error creating opportunity: {str(e)}")
    
    def get_opportunities(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get opportunities with optional filters"""
        query = {}
        if filters:
            if filters.get('account_id'):
                query['account_id'] = filters['account_id']
            if filters.get('stage'):
                query['stage'] = filters['stage']
            if filters.get('owner_id'):
                query['owner_id'] = filters['owner_id']
            if filters.get('is_closed') is not None:
                query['is_closed'] = filters['is_closed']
        
        opportunities = list(self.db[COLLECTIONS['opportunities']].find(query).sort("created_at", -1).limit(limit))
        return [self._serialize_doc(opp) for opp in opportunities]
    
    def get_opportunity_by_id(self, opportunity_id: str) -> Optional[Dict]:
        """Get opportunity by ID"""
        opp = self.db[COLLECTIONS['opportunities']].find_one({"opportunity_id": opportunity_id})
        if opp:
            opp_dict = self._serialize_doc(opp)
            # Add related activities
            opp_dict['activities'] = self.get_activities({"opportunity_id": opportunity_id})
            return opp_dict
        return None
    
    def update_opportunity(self, opportunity_id: str, update_data: Dict) -> bool:
        """Update opportunity"""
        update_data['updated_at'] = datetime.utcnow()
        result = self.db[COLLECTIONS['opportunities']].update_one(
            {"opportunity_id": opportunity_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def close_opportunity(self, opportunity_id: str, won: bool, reason: str = None) -> bool:
        """Close an opportunity"""
        update_data = {
            "is_closed": True,
            "is_won": won,
            "closed_at": datetime.utcnow(),
            "stage": "closed_won" if won else "closed_lost",
            "updated_at": datetime.utcnow()
        }
        
        if reason:
            update_data["closed_reason"] = reason
        
        result = self.db[COLLECTIONS['opportunities']].update_one(
            {"opportunity_id": opportunity_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # === Activity Operations ===
    
    def create_activity(self, activity_data: Dict) -> Dict:
        """Create a new activity"""
        try:
            if "activity_id" not in activity_data or not activity_data["activity_id"]:
                activity_data["activity_id"] = f"ACT_{uuid.uuid4().hex[:8].upper()}"
            
            activity = ActivityModel(**activity_data)
            result = self.db[COLLECTIONS['activities']].insert_one(activity.dict(by_alias=True, exclude={"id"}))
            activity.id = result.inserted_id
            return self._serialize_doc(activity.dict(by_alias=True))
        except Exception as e:
            raise Exception(f"Error creating activity: {str(e)}")
    
    def get_activities(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get activities with optional filters"""
        query = {}
        if filters:
            if filters.get('account_id'):
                query['account_id'] = filters['account_id']
            if filters.get('contact_id'):
                query['contact_id'] = filters['contact_id']
            if filters.get('opportunity_id'):
                query['opportunity_id'] = filters['opportunity_id']
            if filters.get('lead_id'):
                query['lead_id'] = filters['lead_id']
            if filters.get('activity_type'):
                query['activity_type'] = filters['activity_type']
            if filters.get('status'):
                query['status'] = filters['status']
        
        activities = list(self.db[COLLECTIONS['activities']].find(query).sort("created_at", -1).limit(limit))
        return [self._serialize_doc(activity) for activity in activities]
    
    def update_activity(self, activity_id: str, update_data: Dict) -> bool:
        """Update activity"""
        update_data['updated_at'] = datetime.utcnow()
        result = self.db[COLLECTIONS['activities']].update_one(
            {"activity_id": activity_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def complete_activity(self, activity_id: str, outcome: str = None) -> bool:
        """Mark activity as completed"""
        update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if outcome:
            update_data["outcome"] = outcome
        
        result = self.db[COLLECTIONS['activities']].update_one(
            {"activity_id": activity_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # === Task Operations ===
    
    def create_task(self, task_data: Dict) -> Dict:
        """Create a new task"""
        try:
            if "task_id" not in task_data or not task_data["task_id"]:
                task_data["task_id"] = f"TASK_{uuid.uuid4().hex[:8].upper()}"
            
            task = TaskModel(**task_data)
            result = self.db[COLLECTIONS['tasks']].insert_one(task.dict(by_alias=True, exclude={"id"}))
            task.id = result.inserted_id
            return self._serialize_doc(task.dict(by_alias=True))
        except Exception as e:
            raise Exception(f"Error creating task: {str(e)}")
    
    def get_tasks(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get tasks with optional filters"""
        query = {}
        if filters:
            if filters.get('assigned_to'):
                query['assigned_to'] = filters['assigned_to']
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('account_id'):
                query['account_id'] = filters['account_id']
        
        tasks = list(self.db[COLLECTIONS['tasks']].find(query).sort("due_date", 1).limit(limit))
        return [self._serialize_doc(task) for task in tasks]
    
    def update_task(self, task_id: str, update_data: Dict) -> bool:
        """Update task"""
        update_data['updated_at'] = datetime.utcnow()
        result = self.db[COLLECTIONS['tasks']].update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def complete_task(self, task_id: str) -> bool:
        """Mark task as completed"""
        update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = self.db[COLLECTIONS['tasks']].update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # === Helper Methods ===
    
    def _serialize_doc(self, doc: Dict) -> Dict:
        """Convert MongoDB document to JSON-serializable dict"""
        if doc is None:
            return None
        
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        
        # Convert any other ObjectId fields
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, datetime):
                doc[key] = value.isoformat()
        
        return doc
    
    def get_crm_statistics(self) -> Dict:
        """Get CRM statistics"""
        return {
            "total_accounts": self.db[COLLECTIONS['accounts']].count_documents({"status": "active"}),
            "total_contacts": self.db[COLLECTIONS['contacts']].count_documents({"status": "active"}),
            "total_leads": self.db[COLLECTIONS['leads']].count_documents({"converted": False}),
            "open_opportunities": self.db[COLLECTIONS['opportunities']].count_documents({"is_closed": False}),
            "pending_tasks": self.db[COLLECTIONS['tasks']].count_documents({"status": {"$ne": "completed"}}),
            "activities_this_month": self.db[COLLECTIONS['activities']].count_documents({
                "created_at": {"$gte": datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)}
            }),
        }
