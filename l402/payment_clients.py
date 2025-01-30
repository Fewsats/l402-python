"""Payment clients are the interfaces and implementations that allow users to pay for L402 offers."""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_payment_clients.ipynb.

# %% auto 0
__all__ = ['PaymentProvider', 'PaymentRequest', 'CoinbaseProvider', 'get_payment_request', 'Client', 'Fewsats']

# %% ../nbs/01_payment_clients.ipynb 2
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any

from fastcore.utils import *
import fastcore.basics as fc
import os
import json
from .payment_providers import *
from .utils import *
import httpx
from pydantic import BaseModel


# %% ../nbs/01_payment_clients.ipynb 4
class PaymentProvider(ABC):
    """Base class for all payment providers"""
    supported_methods: list[str] = []  # Will be overridden by each provider
    
    @abstractmethod
    def pay(self, *args, **kwargs):
        pass

class PaymentRequest(BaseModel):
    """Represents a payment request to get payment details from a payment provider"""
    offer_id: str
    payment_context_token: str
    payment_method: str
    chain: str = ""
    asset: str = ""


# %% ../nbs/01_payment_clients.ipynb 7
from cdp import *

class CoinbaseProvider(fc.BasicRepr):
    def __init__(self, wallet: Wallet,
                asset: str = 'usdc'):
        store_attr()
        self.supported_methods=["onchain"]
        self.chain = self.wallet.network_id

    # NOTE: in the fewsats example, we will return an async taskID
    def pay(self,
            amount: float,
            address: str,
            asset: str):
        # TODO, return a generic async task 
        return self.wallet.transfer(amount, asset, address).wait()

# %% ../nbs/01_payment_clients.ipynb 14
def get_payment_request(payment_request_url: str,
                        payment_context_token: str,
                        offer_id: str, 
                        payment_method: str, 
                        chain: str = "", 
                        asset: str = ""):
    data = {
        "offer_id": offer_id,
        "payment_method": payment_method,
        "chain": chain,
        "asset": asset,
        "payment_context_token": payment_context_token
    }
    r = httpx.post(payment_request_url, json=data)
    r.raise_for_status()
    return r.json()


# %% ../nbs/01_payment_clients.ipynb 17
class Client(fc.BasicRepr):
    def __init__(self, lightning_provider = None, 
                 credit_card_provider = None, 
                 onchain_provider = None,
                 fewsats_provider = None):
        store_attr()
        self.lightning_provider = lightning_provider
        self.credit_card_provider = credit_card_provider
        self.onchain_provider = onchain_provider
        self.fewsats_provider = fewsats_provider


    def pay(self, ofr_body: dict): # ofr is the l402 offers response dictionary
        "Pay for an offer"
        # this actually does 3 things
        # 1. Selects offer
        # 2. Gets payment request details
        # 3. Uses user-provided payment method
        
        ofr = L402Response(**ofr_body)
        if len(ofr.offers) != 1: raise ValueError("Only one offer is supported")
        o = first(ofr.offers)

        if self.fewsats_provider:
            return self.fewsats_provider.pay(ofr_body)
        elif 'onchain' in o.payment_methods and self.onchain_provider:
            r = get_payment_request(ofr.payment_request_url, ofr.payment_context_token, o.offer_id, 'onchain', self.onchain_provider.chain, self.onchain_provider.asset)

            return self.onchain_provider.pay(o.amount, r['payment_request']['address'], r['payment_request']['asset'])
            
        # elif 'lightning' in o.payment_methods and self.lightning_provider:
        # elif 'credit_card' in o.payment_methods and self.credit_card_provider:
        else:
            raise ValueError(f"No payment provider available for {ofr.offers[0].payment_methods}")


# %% ../nbs/01_payment_clients.ipynb 20
# class PaymentStatus:
#     PENDING = "pending"
#     COMPLETED = "completed"
#     FAILED = "failed"
#     EXPIRED = "expired"

#| export

class Fewsats:
    def __init__(self, api_key: str = None, base_url: str = "https://hub-5n97k.ondigitalocean.app"):
        self.api_key = api_key or os.environ.get("FEWSATS_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided and FEWSATS_API_KEY environment variable is not set")
        self.base_url = base_url
        self.client = httpx.Client()
        self.client.headers.update({"Authorization": f"Token {self.api_key}"})


    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        response = self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def get_payment_methods(self) -> List[Dict[str, Any]]:
        """Retrieve the user's payment methods.
        
        Returns:
            List[Dict[str, Any]]: A list of payment methods associated with the user's account.
        """
        return self._request("GET", "v0/stripe/payment-methods")


    def pay(self, ofr: dict):
        data = {
            "payment_request_url": ofr["payment_request_url"],
            "payment_context_token": ofr["payment_context_token"],
            "payment_method": "onchain",
            "offer": first(ofr["offers"])
        }
        print(data)
        print(self.base_url)
        print(self.api_key)
        return self._request("POST", "v0/l402/purchases/from-offer", json=data)

# %% ../nbs/01_payment_clients.ipynb 25
@patch
def _pay_onchain(self: Fewsats, address: str,
                    amount: str,
                    chain: str = '',
                    asset: str = ''):
    data = {
        "address": address,
        "amount": str(amount),
        "chain": chain,
        "asset": asset,
    }
    print(data)
    return self._request("POST", "v0/l402/purchases/onchain", json=data)

