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
from config import ETH_NETWORKS, DEFAULT_NETWORK, CONTRACT_ADDRESSES, GAS_LIMIT, GAS_PRICE_MULTIPLIER

class WalletManager:
    def __init__(self):
        """Initialize the wallet manager with default network settings"""
        self.network = DEFAULT_NETWORK
        self.web3 = Web3(Web3.HTTPProvider(ETH_NETWORKS[DEFAULT_NETWORK]['rpc_url']))
        self.connected_wallets = {}
        self.transaction_history = {}
        self.logger = logging.getLogger('WalletManager')
        
        # Create transaction history directory if it doesn't exist
        self.history_dir = 'transaction_history'
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
            
    def connect_wallet(self, address):
        """
        Connect a wallet and store its information
        
        Args:
            address (str): Ethereum wallet address
            
        Returns:
            dict: Wallet information including balance and network
        """
        try:
            # Convert address to checksum format
            address = self.web3.to_checksum_address(address)
            
            if not self.web3.is_address(address):
                raise ValueError("Invalid Ethereum address")
                
            # Get wallet balance
            balance = self.web3.eth.get_balance(address)
            balance_eth = self.web3.from_wei(balance, 'ether')
            
            # Store wallet information
            self.connected_wallets[address] = {
                'address': address,
                'balance': balance_eth,
                'network': self.network,
                'connected_at': datetime.now().isoformat()
            }
            
            # Load transaction history
            self._load_transaction_history(address)
            
            return self.connected_wallets[address]
            
        except Exception as e:
            self.logger.error(f"Error connecting wallet {address}: {e}")
            raise
            
    def disconnect_wallet(self, address):
        """
        Disconnect a wallet and save its transaction history
        
        Args:
            address (str): Ethereum wallet address
        """
        if address in self.connected_wallets:
            self._save_transaction_history(address)
            del self.connected_wallets[address]
            
    def switch_network(self, network):
        """
        Switch to a different Ethereum network
        
        Args:
            network (str): Network name ('mainnet' or 'testnet')
        """
        if network not in ETH_NETWORKS:
            raise ValueError(f"Invalid network: {network}")
            
        self.network = network
        self.web3 = Web3(Web3.HTTPProvider(ETH_NETWORKS[network]['rpc_url']))
        
        # Update network for all connected wallets
        for address in self.connected_wallets:
            self.connected_wallets[address]['network'] = network
            
    def get_transaction_history(self, address):
        """
        Get transaction history for a wallet
        
        Args:
            address (str): Ethereum wallet address
            
        Returns:
            list: List of transactions
        """
        if address not in self.transaction_history:
            self._load_transaction_history(address)
        return self.transaction_history.get(address, [])
        
    def add_transaction(self, address, tx_hash, tx_type, amount, token=None):
        """
        Add a transaction to the history
        
        Args:
            address (str): Wallet address
            tx_hash (str): Transaction hash
            tx_type (str): Transaction type (e.g., 'swap', 'transfer')
            amount (float): Transaction amount
            token (str, optional): Token symbol if applicable
        """
        if address not in self.transaction_history:
            self.transaction_history[address] = []
            
        transaction = {
            'hash': tx_hash,
            'type': tx_type,
            'amount': amount,
            'token': token,
            'network': self.network,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        self.transaction_history[address].append(transaction)
        self._save_transaction_history(address)
        
    def update_transaction_status(self, address, tx_hash, status):
        """
        Update the status of a transaction
        
        Args:
            address (str): Wallet address
            tx_hash (str): Transaction hash
            status (str): New status ('pending', 'confirmed', 'failed')
        """
        if address in self.transaction_history:
            for tx in self.transaction_history[address]:
                if tx['hash'] == tx_hash:
                    tx['status'] = status
                    self._save_transaction_history(address)
                    break
                    
    def _load_transaction_history(self, address):
        """Load transaction history from file"""
        history_file = os.path.join(self.history_dir, f"{address}.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    self.transaction_history[address] = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading transaction history for {address}: {e}")
                
    def _save_transaction_history(self, address):
        """Save transaction history to file"""
        history_file = os.path.join(self.history_dir, f"{address}.json")
        try:
            with open(history_file, 'w') as f:
                json.dump(self.transaction_history[address], f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving transaction history for {address}: {e}")
            
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