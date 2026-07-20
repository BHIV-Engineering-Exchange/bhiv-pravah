#!/usr/bin/env python3
"""
CRM Service layer for AI Agent Logistics + CRM System
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import uuid

from .models import (
    SessionLocal, Account, Contact, Lead, Opportunity, Activity,
    CommunicationLog, Task, Note
)

class CRMService:
    """CRM service for managing accounts, contacts, leads, and opportunities"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    # === Account Operations ===
    
    def create_account(self, account_data: Dict) -> Dict:
        """Create a new account"""
        try:
            account_id = account_data.get('account_id') or f"ACC_{uuid.uuid4().hex[:8].upper()}"
            
            account = Account(
                account_id=account_id,
                name=account_data['name'],
                account_type=account_data.get('account_type', 'customer'),
                industry=account_data.get('industry'),
                website=account_data.get('website'),
                phone=account_data.get('phone'),
                email=account_data.get('email'),
                billing_address=account_data.get('billing_address'),
                shipping_address=account_data.get('shipping_address'),
                city=account_data.get('city'),
                state=account_data.get('state'),
                country=account_data.get('country'),
                postal_code=account_data.get('postal_code'),
                annual_revenue=account_data.get('annual_revenue'),
                employee_count=account_data.get('employee_count'),
                territory=account_data.get('territory'),
                parent_account_id=account_data.get('parent_account_id'),
                account_manager_id=account_data.get('account_manager_id'),
                status=account_data.get('status', 'active'),
                lifecycle_stage=account_data.get('lifecycle_stage', 'prospect'),
                created_by=account_data.get('created_by'),
                notes=account_data.get('notes')
            )
            
            self.db.add(account)
            self.db.commit()
            
            return self._account_to_dict(account)
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error creating account: {str(e)}")
    
    def get_accounts(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get accounts with optional filters"""
        query = self.db.query(Account)
        
        if filters:
            if filters.get('account_type'):
                query = query.filter(Account.account_type == filters['account_type'])
            if filters.get('status'):
                query = query.filter(Account.status == filters['status'])
            if filters.get('territory'):
                query = query.filter(Account.territory == filters['territory'])
            if filters.get('account_manager_id'):
                query = query.filter(Account.account_manager_id == filters['account_manager_id'])
        
        accounts = query.order_by(desc(Account.created_at)).limit(limit).all()
        return [self._account_to_dict(account) for account in accounts]
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Get account by ID with full details"""
        account = self.db.query(Account).filter(Account.account_id == account_id).first()
        if account:
            account_dict = self._account_to_dict(account)
            
            # Add related data
            account_dict['contacts'] = [self._contact_to_dict(c) for c in account.contacts]
            account_dict['opportunities'] = [self._opportunity_to_dict(o) for o in account.opportunities]
            account_dict['activities'] = [self._activity_to_dict(a) for a in account.activities[-10:]]  # Last 10 activities
            
            return account_dict
        return None
    
    def update_account(self, account_id: str, update_data: Dict) -> Optional[Dict]:
        """Update account"""
        account = self.db.query(Account).filter(Account.account_id == account_id).first()
        if account:
            for key, value in update_data.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            
            account.updated_at = datetime.utcnow()
            self.db.commit()
            return self._account_to_dict(account)
        return None
    
    # === Contact Operations ===
    
    def create_contact(self, contact_data: Dict) -> Dict:
        """Create a new contact"""
        try:
            contact_id = contact_data.get('contact_id') or f"CON_{uuid.uuid4().hex[:8].upper()}"
            
            contact = Contact(
                contact_id=contact_id,
                account_id=contact_data['account_id'],
                first_name=contact_data['first_name'],
                last_name=contact_data['last_name'],
                title=contact_data.get('title'),
                department=contact_data.get('department'),
                email=contact_data.get('email'),
                phone=contact_data.get('phone'),
                mobile=contact_data.get('mobile'),
                contact_role=contact_data.get('contact_role', 'contact'),
                is_primary=contact_data.get('is_primary', False),
                reports_to_id=contact_data.get('reports_to_id'),
                status=contact_data.get('status', 'active'),
                created_by=contact_data.get('created_by'),
                notes=contact_data.get('notes')
            )
            
            self.db.add(contact)
            self.db.commit()
            
            return self._contact_to_dict(contact)
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error creating contact: {str(e)}")
    
    def get_contacts(self, account_id: str = None, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get contacts with optional filters"""
        query = self.db.query(Contact)
        
        if account_id:
            query = query.filter(Contact.account_id == account_id)
        
        if filters:
            if filters.get('contact_role'):
                query = query.filter(Contact.contact_role == filters['contact_role'])
            if filters.get('status'):
                query = query.filter(Contact.status == filters['status'])
        
        contacts = query.order_by(desc(Contact.created_at)).limit(limit).all()
        return [self._contact_to_dict(contact) for contact in contacts]
    
    def get_contact_by_id(self, contact_id: str) -> Optional[Dict]:
        """Get contact by ID"""
        contact = self.db.query(Contact).filter(Contact.contact_id == contact_id).first()
        if contact:
            return self._contact_to_dict(contact)
        return None
    
    # === Lead Operations ===
    
    def create_lead(self, lead_data: Dict) -> Dict:
        """Create a new lead"""
        try:
            lead_id = lead_data.get('lead_id') or f"LEAD_{uuid.uuid4().hex[:8].upper()}"
            
            lead = Lead(
                lead_id=lead_id,
                first_name=lead_data.get('first_name'),
                last_name=lead_data.get('last_name'),
                company=lead_data.get('company'),
                title=lead_data.get('title'),
                email=lead_data.get('email'),
                phone=lead_data.get('phone'),
                lead_source=lead_data.get('lead_source'),
                lead_status=lead_data.get('lead_status', 'new'),
                lead_stage=lead_data.get('lead_stage', 'inquiry'),
                budget=lead_data.get('budget'),
                timeline=lead_data.get('timeline'),
                authority=lead_data.get('authority'),
                need=lead_data.get('need'),
                assigned_to=lead_data.get('assigned_to'),
                territory=lead_data.get('territory'),
                created_by=lead_data.get('created_by'),
                notes=lead_data.get('notes')
            )
            
            self.db.add(lead)
            self.db.commit()
            
            return self._lead_to_dict(lead)
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error creating lead: {str(e)}")
    
    def get_leads(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get leads with optional filters"""
        query = self.db.query(Lead)
        
        if filters:
            if filters.get('lead_status'):
                query = query.filter(Lead.lead_status == filters['lead_status'])
            if filters.get('lead_source'):
                query = query.filter(Lead.lead_source == filters['lead_source'])
            if filters.get('assigned_to'):
                query = query.filter(Lead.assigned_to == filters['assigned_to'])
            if filters.get('converted') is not None:
                query = query.filter(Lead.converted == filters['converted'])
        
        leads = query.order_by(desc(Lead.created_at)).limit(limit).all()
        return [self._lead_to_dict(lead) for lead in leads]
    
    def get_lead_by_id(self, lead_id: str) -> Optional[Dict]:
        """Get lead by ID"""
        lead = self.db.query(Lead).filter(Lead.lead_id == lead_id).first()
        if lead:
            return self._lead_to_dict(lead)
        return None
    
    def convert_lead_to_opportunity(self, lead_id: str, opportunity_data: Dict) -> Dict:
        """Convert lead to opportunity"""
        try:
            lead = self.db.query(Lead).filter(Lead.lead_id == lead_id).first()
            if not lead:
                raise Exception("Lead not found")
            
            # Create or find account
            account_id = opportunity_data.get('account_id')
            if not account_id:
                # Create new account from lead
                account_data = {
                    'name': lead.company or f"{lead.first_name} {lead.last_name}",
                    'account_type': 'customer',
                    'phone': lead.phone,
                    'email': lead.email,
                    'created_by': opportunity_data.get('created_by')
                }
                account = self.create_account(account_data)
                account_id = account['account_id']
            
            # Create contact from lead
            contact_data = {
                'account_id': account_id,
                'first_name': lead.first_name or 'Unknown',
                'last_name': lead.last_name or 'Contact',
                'title': lead.title,
                'email': lead.email,
                'phone': lead.phone,
                'contact_role': 'decision_maker',
                'is_primary': True,
                'created_by': opportunity_data.get('created_by')
            }
            contact = self.create_contact(contact_data)
            
            # Create opportunity
            opportunity_data.update({
                'account_id': account_id,
                'primary_contact_id': contact['contact_id'],
                'name': opportunity_data.get('name') or f"Opportunity from {lead.full_name}",
                'description': lead.need
            })
            opportunity = self.create_opportunity(opportunity_data)
            
            # Update lead as converted
            lead.converted = True
            lead.converted_at = datetime.utcnow()
            lead.converted_to_account_id = account_id
            lead.converted_to_opportunity_id = opportunity['opportunity_id']
            lead.lead_status = 'converted'
            
            self.db.commit()
            
            return {
                'lead': self._lead_to_dict(lead),
                'account': account,
                'contact': contact,
                'opportunity': opportunity
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error converting lead: {str(e)}")
    
    # === Opportunity Operations ===
    
    def create_opportunity(self, opportunity_data: Dict) -> Dict:
        """Create a new opportunity"""
        try:
            opportunity_id = opportunity_data.get('opportunity_id') or f"OPP_{uuid.uuid4().hex[:8].upper()}"
            
            opportunity = Opportunity(
                opportunity_id=opportunity_id,
                account_id=opportunity_data['account_id'],
                primary_contact_id=opportunity_data.get('primary_contact_id'),
                name=opportunity_data['name'],
                description=opportunity_data.get('description'),
                opportunity_type=opportunity_data.get('opportunity_type', 'new_business'),
                stage=opportunity_data.get('stage', 'prospecting'),
                probability=opportunity_data.get('probability', 0.0),
                amount=opportunity_data.get('amount'),
                currency=opportunity_data.get('currency', 'USD'),
                expected_revenue=opportunity_data.get('expected_revenue'),
                close_date=opportunity_data.get('close_date'),
                owner_id=opportunity_data.get('owner_id'),
                requirements=opportunity_data.get('requirements'),
                products_interested=opportunity_data.get('products_interested'),
                competitors=opportunity_data.get('competitors'),
                risks=opportunity_data.get('risks'),
                created_by=opportunity_data.get('created_by'),
                notes=opportunity_data.get('notes')
            )
            
            self.db.add(opportunity)
            self.db.commit()
            
            return self._opportunity_to_dict(opportunity)
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error creating opportunity: {str(e)}")
    
    def get_opportunities(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get opportunities with optional filters"""
        query = self.db.query(Opportunity)
        
        if filters:
            if filters.get('stage'):
                query = query.filter(Opportunity.stage == filters['stage'])
            if filters.get('owner_id'):
                query = query.filter(Opportunity.owner_id == filters['owner_id'])
            if filters.get('account_id'):
                query = query.filter(Opportunity.account_id == filters['account_id'])
            if filters.get('is_closed') is not None:
                query = query.filter(Opportunity.is_closed == filters['is_closed'])
            if filters.get('close_date_from'):
                query = query.filter(Opportunity.close_date >= filters['close_date_from'])
            if filters.get('close_date_to'):
                query = query.filter(Opportunity.close_date <= filters['close_date_to'])
        
        opportunities = query.order_by(desc(Opportunity.created_at)).limit(limit).all()
        return [self._opportunity_to_dict(opportunity) for opportunity in opportunities]
    
    def get_opportunity_by_id(self, opportunity_id: str) -> Optional[Dict]:
        """Get opportunity by ID"""
        opportunity = self.db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
        if opportunity:
            return self._opportunity_to_dict(opportunity)
        return None
    
    def update_opportunity_stage(self, opportunity_id: str, stage: str, probability: float = None) -> Optional[Dict]:
        """Update opportunity stage and probability"""
        opportunity = self.db.query(Opportunity).filter(Opportunity.opportunity_id == opportunity_id).first()
        if opportunity:
            opportunity.stage = stage
            if probability is not None:
                opportunity.probability = probability
            
            # Handle closed stages
            if stage in ['closed_won', 'closed_lost']:
                opportunity.is_closed = True
                opportunity.is_won = (stage == 'closed_won')
                opportunity.closed_at = datetime.utcnow()
            
            opportunity.updated_at = datetime.utcnow()
            self.db.commit()
            return self._opportunity_to_dict(opportunity)
        return None
    
    # === Activity Operations ===
    
    def create_activity(self, activity_data: Dict) -> Dict:
        """Create a new activity"""
        try:
            activity_id = activity_data.get('activity_id') or f"ACT_{uuid.uuid4().hex[:8].upper()}"
            
            activity = Activity(
                activity_id=activity_id,
                subject=activity_data['subject'],
                description=activity_data.get('description'),
                activity_type=activity_data['activity_type'],
                status=activity_data.get('status', 'planned'),
                priority=activity_data.get('priority', 'medium'),
                due_date=activity_data.get('due_date'),
                start_time=activity_data.get('start_time'),
                end_time=activity_data.get('end_time'),
                duration_minutes=activity_data.get('duration_minutes'),
                account_id=activity_data.get('account_id'),
                contact_id=activity_data.get('contact_id'),
                opportunity_id=activity_data.get('opportunity_id'),
                lead_id=activity_data.get('lead_id'),
                assigned_to=activity_data.get('assigned_to'),
                created_by=activity_data.get('created_by'),
                communication_type=activity_data.get('communication_type'),
                outcome=activity_data.get('outcome'),
                next_steps=activity_data.get('next_steps'),
                location=activity_data.get('location'),
                latitude=activity_data.get('latitude'),
                longitude=activity_data.get('longitude')
            )
            
            self.db.add(activity)
            self.db.commit()
            
            return self._activity_to_dict(activity)
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error creating activity: {str(e)}")
    
    def get_activities(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get activities with optional filters"""
        query = self.db.query(Activity)
        
        if filters:
            if filters.get('activity_type'):
                query = query.filter(Activity.activity_type == filters['activity_type'])
            if filters.get('status'):
                query = query.filter(Activity.status == filters['status'])
            if filters.get('assigned_to'):
                query = query.filter(Activity.assigned_to == filters['assigned_to'])
            if filters.get('account_id'):
                query = query.filter(Activity.account_id == filters['account_id'])
            if filters.get('opportunity_id'):
                query = query.filter(Activity.opportunity_id == filters['opportunity_id'])
            if filters.get('lead_id'):
                query = query.filter(Activity.lead_id == filters['lead_id'])
        
        activities = query.order_by(desc(Activity.created_at)).limit(limit).all()
        return [self._activity_to_dict(activity) for activity in activities]
    
    def complete_activity(self, activity_id: str, outcome: str = None, next_steps: str = None) -> Optional[Dict]:
        """Mark activity as completed"""
        activity = self.db.query(Activity).filter(Activity.activity_id == activity_id).first()
        if activity:
            activity.status = 'completed'
            activity.completed_at = datetime.utcnow()
            if outcome:
                activity.outcome = outcome
            if next_steps:
                activity.next_steps = next_steps
            
            self.db.commit()
            return self._activity_to_dict(activity)
        return None
    
    # === Task Operations ===
    
    def create_task(self, task_data: Dict) -> Dict:
        """Create a new task"""
        try:
            task_id = task_data.get('task_id') or f"TASK_{uuid.uuid4().hex[:8].upper()}"
            
            task = Task(
                task_id=task_id,
                title=task_data['title'],
                description=task_data.get('description'),
                task_type=task_data.get('task_type', 'general'),
                priority=task_data.get('priority', 'medium'),
                status=task_data.get('status', 'pending'),
                due_date=task_data.get('due_date'),
                reminder_date=task_data.get('reminder_date'),
                assigned_to=task_data['assigned_to'],
                created_by=task_data.get('created_by'),
                account_id=task_data.get('account_id'),
                contact_id=task_data.get('contact_id'),
                opportunity_id=task_data.get('opportunity_id'),
                lead_id=task_data.get('lead_id')
            )
            
            self.db.add(task)
            self.db.commit()
            
            return self._task_to_dict(task)
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error creating task: {str(e)}")
    
    def get_tasks(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Get tasks with optional filters"""
        query = self.db.query(Task)
        
        if filters:
            if filters.get('status'):
                query = query.filter(Task.status == filters['status'])
            if filters.get('assigned_to'):
                query = query.filter(Task.assigned_to == filters['assigned_to'])
            if filters.get('priority'):
                query = query.filter(Task.priority == filters['priority'])
            if filters.get('account_id'):
                query = query.filter(Task.account_id == filters['account_id'])
            if filters.get('opportunity_id'):
                query = query.filter(Task.opportunity_id == filters['opportunity_id'])
        
        tasks = query.order_by(desc(Task.created_at)).limit(limit).all()
        return [self._task_to_dict(task) for task in tasks]
    
    # === Analytics and Reporting ===
    
    def get_crm_dashboard_data(self) -> Dict:
        """Get CRM dashboard summary data"""
        try:
            # Account metrics
            total_accounts = self.db.query(Account).count()
            active_accounts = self.db.query(Account).filter(Account.status == 'active').count()
            
            # Lead metrics
            total_leads = self.db.query(Lead).count()
            new_leads = self.db.query(Lead).filter(Lead.lead_status == 'new').count()
            converted_leads = self.db.query(Lead).filter(Lead.converted == True).count()
            
            # Opportunity metrics
            total_opportunities = self.db.query(Opportunity).count()
            open_opportunities = self.db.query(Opportunity).filter(Opportunity.is_closed == False).count()
            won_opportunities = self.db.query(Opportunity).filter(Opportunity.is_won == True).count()
            
            # Pipeline value
            pipeline_value = self.db.query(func.sum(Opportunity.amount)).filter(
                Opportunity.is_closed == False
            ).scalar() or 0
            
            # Recent activities
            recent_activities = self.db.query(Activity).order_by(desc(Activity.created_at)).limit(10).all()
            
            # Pending tasks
            pending_tasks = self.db.query(Task).filter(Task.status == 'pending').count()
            
            return {
                'accounts': {
                    'total': total_accounts,
                    'active': active_accounts
                },
                'leads': {
                    'total': total_leads,
                    'new': new_leads,
                    'converted': converted_leads,
                    'conversion_rate': (converted_leads / total_leads * 100) if total_leads > 0 else 0
                },
                'opportunities': {
                    'total': total_opportunities,
                    'open': open_opportunities,
                    'won': won_opportunities,
                    'win_rate': (won_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0,
                    'pipeline_value': pipeline_value
                },
                'activities': {
                    'recent': [self._activity_to_dict(a) for a in recent_activities]
                },
                'tasks': {
                    'pending': pending_tasks
                }
            }
            
        except Exception as e:
            raise Exception(f"Error getting dashboard data: {str(e)}")
    
    # === Helper Methods ===
    
    def _account_to_dict(self, account: Account) -> Dict:
        """Convert Account model to dictionary"""
        return {
            'account_id': account.account_id,
            'name': account.name,
            'account_type': account.account_type,
            'industry': account.industry,
            'website': account.website,
            'phone': account.phone,
            'email': account.email,
            'billing_address': account.billing_address,
            'shipping_address': account.shipping_address,
            'city': account.city,
            'state': account.state,
            'country': account.country,
            'postal_code': account.postal_code,
            'annual_revenue': account.annual_revenue,
            'employee_count': account.employee_count,
            'territory': account.territory,
            'parent_account_id': account.parent_account_id,
            'account_manager_id': account.account_manager_id,
            'status': account.status,
            'lifecycle_stage': account.lifecycle_stage,
            'created_at': account.created_at.isoformat() if account.created_at else None,
            'updated_at': account.updated_at.isoformat() if account.updated_at else None,
            'created_by': account.created_by,
            'notes': account.notes
        }
    
    def _contact_to_dict(self, contact: Contact) -> Dict:
        """Convert Contact model to dictionary"""
        return {
            'contact_id': contact.contact_id,
            'account_id': contact.account_id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'full_name': contact.full_name,
            'title': contact.title,
            'department': contact.department,
            'email': contact.email,
            'phone': contact.phone,
            'mobile': contact.mobile,
            'contact_role': contact.contact_role,
            'is_primary': contact.is_primary,
            'reports_to_id': contact.reports_to_id,
            'status': contact.status,
            'created_at': contact.created_at.isoformat() if contact.created_at else None,
            'updated_at': contact.updated_at.isoformat() if contact.updated_at else None,
            'created_by': contact.created_by,
            'notes': contact.notes
        }
    
    def _lead_to_dict(self, lead: Lead) -> Dict:
        """Convert Lead model to dictionary"""
        return {
            'lead_id': lead.lead_id,
            'first_name': lead.first_name,
            'last_name': lead.last_name,
            'full_name': lead.full_name,
            'company': lead.company,
            'title': lead.title,
            'email': lead.email,
            'phone': lead.phone,
            'lead_source': lead.lead_source,
            'lead_status': lead.lead_status,
            'lead_stage': lead.lead_stage,
            'budget': lead.budget,
            'timeline': lead.timeline,
            'authority': lead.authority,
            'need': lead.need,
            'assigned_to': lead.assigned_to,
            'territory': lead.territory,
            'converted': lead.converted,
            'converted_at': lead.converted_at.isoformat() if lead.converted_at else None,
            'converted_to_account_id': lead.converted_to_account_id,
            'converted_to_opportunity_id': lead.converted_to_opportunity_id,
            'created_at': lead.created_at.isoformat() if lead.created_at else None,
            'updated_at': lead.updated_at.isoformat() if lead.updated_at else None,
            'created_by': lead.created_by,
            'notes': lead.notes
        }
    
    def _opportunity_to_dict(self, opportunity: Opportunity) -> Dict:
        """Convert Opportunity model to dictionary"""
        return {
            'opportunity_id': opportunity.opportunity_id,
            'account_id': opportunity.account_id,
            'primary_contact_id': opportunity.primary_contact_id,
            'name': opportunity.name,
            'description': opportunity.description,
            'opportunity_type': opportunity.opportunity_type,
            'stage': opportunity.stage,
            'probability': opportunity.probability,
            'amount': opportunity.amount,
            'currency': opportunity.currency,
            'expected_revenue': opportunity.expected_revenue,
            'close_date': opportunity.close_date.isoformat() if opportunity.close_date else None,
            'owner_id': opportunity.owner_id,
            'requirements': opportunity.requirements,
            'products_interested': opportunity.products_interested,
            'competitors': opportunity.competitors,
            'risks': opportunity.risks,
            'is_closed': opportunity.is_closed,
            'is_won': opportunity.is_won,
            'closed_at': opportunity.closed_at.isoformat() if opportunity.closed_at else None,
            'closed_reason': opportunity.closed_reason,
            'created_at': opportunity.created_at.isoformat() if opportunity.created_at else None,
            'updated_at': opportunity.updated_at.isoformat() if opportunity.updated_at else None,
            'created_by': opportunity.created_by,
            'notes': opportunity.notes
        }
    
    def _activity_to_dict(self, activity: Activity) -> Dict:
        """Convert Activity model to dictionary"""
        return {
            'activity_id': activity.activity_id,
            'subject': activity.subject,
            'description': activity.description,
            'activity_type': activity.activity_type,
            'status': activity.status,
            'priority': activity.priority,
            'due_date': activity.due_date.isoformat() if activity.due_date else None,
            'start_time': activity.start_time.isoformat() if activity.start_time else None,
            'end_time': activity.end_time.isoformat() if activity.end_time else None,
            'duration_minutes': activity.duration_minutes,
            'account_id': activity.account_id,
            'contact_id': activity.contact_id,
            'opportunity_id': activity.opportunity_id,
            'lead_id': activity.lead_id,
            'assigned_to': activity.assigned_to,
            'created_by': activity.created_by,
            'communication_type': activity.communication_type,
            'outcome': activity.outcome,
            'next_steps': activity.next_steps,
            'location': activity.location,
            'latitude': activity.latitude,
            'longitude': activity.longitude,
            'created_at': activity.created_at.isoformat() if activity.created_at else None,
            'updated_at': activity.updated_at.isoformat() if activity.updated_at else None,
            'completed_at': activity.completed_at.isoformat() if activity.completed_at else None
        }
    
    def _task_to_dict(self, task: Task) -> Dict:
        """Convert Task model to dictionary"""
        return {
            'task_id': task.task_id,
            'title': task.title,
            'description': task.description,
            'task_type': task.task_type,
            'priority': task.priority,
            'status': task.status,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'reminder_date': task.reminder_date.isoformat() if task.reminder_date else None,
            'assigned_to': task.assigned_to,
            'created_by': task.created_by,
            'account_id': task.account_id,
            'contact_id': task.contact_id,
            'opportunity_id': task.opportunity_id,
            'lead_id': task.lead_id,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'updated_at': task.updated_at.isoformat() if task.updated_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        }