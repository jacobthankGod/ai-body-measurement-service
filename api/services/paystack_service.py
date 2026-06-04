"""
Paystack Service
==============
Handles integration with Paystack payment API.
"""
import httpx
import hashlib
import hmac
import json
from typing import Optional, Dict, Any


class PaystackService:
    """Service for interacting with Paystack API"""
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self, secret_key: str, public_key: str):
        """
        Initialize Paystack service.
        
        Args:
            secret_key: Paystack secret key for server-side operations
            public_key: Paystack public key for client-side operations
        """
        self.secret_key = secret_key
        self.public_key = public_key
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                'Authorization': f'Bearer {secret_key}',
                'Content-Type': 'application/json'
            }
        )
    
    def initialize_payment(
        self,
        email: str,
        amount: int,
        reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize a payment transaction with Paystack.
        
        Args:
            email: Customer email
            amount: Amount in kobo (smallest currency unit)
            reference: Optional custom reference (Paystack generates one if None)
            metadata: Optional metadata to attach to transaction
        
        Returns:
            Response from Paystack API
        """
        payload = {
            'email': email,
            'amount': amount,
        }
        
        if reference:
            payload['reference'] = reference
        
        if metadata:
            payload['metadata'] = metadata
        
        try:
            response = self.client.post('/transaction/initialize', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                'status': False,
                'message': f'Failed to initialize payment: {str(e)}'
            }
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """
        Verify a payment transaction.
        
        Args:
            reference: Paystack transaction reference
        
        Returns:
            Verification result with transaction details
        """
        try:
            response = self.client.get(f'/transaction/verify/{reference}')
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                'status': False,
                'message': f'Failed to verify payment: {str(e)}'
            }
    
    def list_transactions(
        self,
        limit: int = 10,
        page: int = 1,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List transactions.
        
        Args:
            limit: Number of transactions to retrieve
            page: Page number
            customer_id: Optional customer ID to filter by
        
        Returns:
            List of transactions
        """
        params = {
            'perPage': limit,
            'page': page
        }
        
        if customer_id:
            params['customer'] = customer_id
        
        try:
            response = self.client.get('/transaction', params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                'status': False,
                'message': f'Failed to list transactions: {str(e)}'
            }
    
    def create_customer(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a customer record on Paystack.
        
        Args:
            email: Customer email
            first_name: Optional first name
            last_name: Optional last name
            phone: Optional phone number
        
        Returns:
            Customer creation result
        """
        payload = {'email': email}
        
        if first_name:
            payload['first_name'] = first_name
        if last_name:
            payload['last_name'] = last_name
        if phone:
            payload['phone'] = phone
        
        try:
            response = self.client.post('/customer', json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                'status': False,
                'message': f'Failed to create customer: {str(e)}'
            }
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance.
        
        Returns:
            Account balance information
        """
        try:
            response = self.client.get('/balance')
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                'status': False,
                'message': f'Failed to get balance: {str(e)}'
            }
    
    def verify_webhook_signature(self, request_body: Any, signature: str) -> bool:
        """
        Verify Paystack webhook signature.
        
        Args:
            request_body: Request body (dict or JSON string)
            signature: x-paystack-signature header value
        
        Returns:
            True if signature is valid, False otherwise
        """
        if isinstance(request_body, dict):
            request_body = json.dumps(request_body)
        
        hash_object = hmac.new(
            self.secret_key.encode(),
            request_body.encode() if isinstance(request_body, str) else request_body,
            hashlib.sha512
        )
        
        computed_signature = hash_object.hexdigest()
        return computed_signature == signature
    
    def __del__(self):
        """Cleanup HTTP client"""
        self.client.close()
