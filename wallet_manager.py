"""
This module handles Ethereum wallet interactions and transaction management.
It includes functionality for:
- Wallet connection and management
- Transaction creation and signing
- Transaction history tracking
- Gas price estimation
- Network switching
"""

from web3 import Web3
from eth_account import Account
import json
import logging
from datetime import datetime
import os
from config import SOLANA_NETWORKS, DEFAULT_NETWORK, PROGRAM_IDS
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.publickey import PublicKey
import base58

class WalletManager:
    def __init__(self):
        """Initialize the wallet manager with default network settings"""
        self.network = DEFAULT_NETWORK
        self.web3 = Web3(Web3.HTTPProvider(SOLANA_NETWORKS[DEFAULT_NETWORK]['rpc_url']))
        self.connected_wallets = {}
        self.transaction_history = {}
        self.logger = logging.getLogger('WalletManager')
        self.current_network = DEFAULT_NETWORK
        self.client = Client(SOLANA_NETWORKS[DEFAULT_NETWORK]['rpc_url'])
        
        # Create transaction history directory if it doesn't exist
        self.history_dir = 'transaction_history'
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
            
    def connect_wallet(self, address, public_key=None):
        """Connect a Solana wallet"""
        try:
            # Initialize wallet info
            wallet_info = {
                'address': address,
                'public_key': public_key,
                'network': self.current_network,
                'balance': 0,
                'connected': True
            }
            
            # Get initial balance
            balance = self.client.get_balance(address)
            wallet_info['balance'] = balance['result']['value'] / 1e9  # Convert lamports to SOL
            
            # Store wallet info
            self.connected_wallets[address] = wallet_info
            return wallet_info
            
        except Exception as e:
            logging.error(f"Error connecting wallet: {e}")
            raise
            
    def disconnect_wallet(self, address):
        """Disconnect a Solana wallet"""
        if address in self.connected_wallets:
            del self.connected_wallets[address]
            
    def switch_network(self, network):
        """Switch Solana network"""
        if network not in SOLANA_NETWORKS:
            raise ValueError(f"Invalid network: {network}")
            
        self.network = network
        self.web3 = Web3(Web3.HTTPProvider(SOLANA_NETWORKS[network]['rpc_url']))
        self.current_network = network
        self.client = Client(SOLANA_NETWORKS[network]['rpc_url'])
        
        # Update all connected wallets
        for address in self.connected_wallets:
            try:
                balance = self.client.get_balance(address)
                self.connected_wallets[address]['balance'] = balance['result']['value'] / 1e9
                self.connected_wallets[address]['network'] = network
            except Exception as e:
                logging.error(f"Error updating wallet balance for {address}: {e}")
            
    def get_balance(self, address):
        """Get wallet balance"""
        try:
            balance = self.client.get_balance(address)
            return balance['result']['value'] / 1e9
        except Exception as e:
            logging.error(f"Error getting balance for {address}: {e}")
            return 0
            
    def get_transaction_history(self, address, limit=10):
        """Get transaction history for a wallet"""
        try:
            # Get recent signatures
            signatures = self.client.get_signatures_for_address(
                PublicKey(address),
                limit=limit
            )
            
            transactions = []
            for sig_info in signatures['result']:
                # Get transaction details
                tx = self.client.get_transaction(
                    sig_info['signature'],
                    commitment=Commitment("confirmed")
                )
                
                if tx['result']:
                    transactions.append({
                        'signature': sig_info['signature'],
                        'timestamp': sig_info['blockTime'],
                        'status': 'confirmed',
                        'fee': tx['result']['meta']['fee'] / 1e9,
                        'type': self._determine_transaction_type(tx['result'])
                    })
                    
            return transactions
            
        except Exception as e:
            logging.error(f"Error getting transaction history for {address}: {e}")
            return []
            
    def _determine_transaction_type(self, tx):
        """Determine the type of transaction"""
        # This is a simplified version - you might want to add more transaction types
        if 'instructions' in tx['transaction']['message']:
            instructions = tx['transaction']['message']['instructions']
            if any(ix['programId'] == 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA' for ix in instructions):
                return 'token_transfer'
            elif any(ix['programId'] == '11111111111111111111111111111111' for ix in instructions):
                return 'sol_transfer'
        return 'unknown'
        
    def send_transaction(self, from_address, to_address, amount, private_key=None):
        """Send a transaction"""
        try:
            # Create transaction
            transaction = Transaction()
            
            # Add transfer instruction
            transaction.add_transfer(
                from_pubkey=PublicKey(from_address),
                to_pubkey=PublicKey(to_address),
                lamports=int(amount * 1e9)  # Convert SOL to lamports
            )
            
            # Sign transaction if private key is provided
            if private_key:
                keypair = Keypair.from_secret_key(base58.b58decode(private_key))
                transaction.sign(keypair)
                
            # Send transaction
            result = self.client.send_transaction(
                transaction,
                opts={"skip_confirmation": False}
            )
            
            return {
                'status': 'success',
                'signature': result['result']
            }
            
        except Exception as e:
            logging.error(f"Error sending transaction: {e}")
            raise
        
    def estimate_gas_price(self):
        """
        Estimate current gas price with multiplier
        
        Returns:
            int: Estimated gas price in wei
        """
        try:
            base_gas_price = self.web3.eth.gas_price
            return int(base_gas_price * GAS_PRICE_MULTIPLIER)
        except Exception as e:
            self.logger.error(f"Error estimating gas price: {e}")
            return None 