import os
import json
import sys
import time
from datetime import datetime, timedelta
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Load environment variables
load_dotenv()

def load_addresses(use_fallback=False):
    """Load addresses from address_list.json"""
    try:
        with open('address_list.json', 'r') as f:
            data = json.load(f)
            return data.get('addresses', [])
    except FileNotFoundError:
        if use_fallback:
            # Create the file with an empty list if it doesn't exist
            save_addresses([])
            return []
        raise
    except Exception as e:
        logger.error(f"Error loading addresses: {str(e)}")
        return []

def save_addresses(addresses):
    """Save addresses to address_list.json"""
    try:
        with open('address_list.json', 'w') as f:
            json.dump({'addresses': addresses}, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving addresses: {str(e)}")
        raise

# Default values
DEFAULT_HYB_AMOUNT = 0.001
DEFAULT_INTERVAL = 1
DEFAULT_DURATION = float('inf')  # Infinite duration

# Chain configuration
CHAIN_CONFIG = {
    'hybrid_testnet': {
        'rpc_url': 'https://hybrid-testnet.rpc.caldera.xyz/http',
        'chain_id': 1225,
        'native_token': 'HYB',
        'explorer': 'https://hybrid-testnet.explorer.caldera.xyz'
    }
}

class HYBDistributor:
    def __init__(self, private_key, logger=None):
        """
        Initialize the HYB token distributor
        private_key: The private key for the sending wallet
        logger: Optional logger instance for logging messages
        """
        # Initialize Web3 with Hybrid testnet
        self.chain_config = CHAIN_CONFIG['hybrid_testnet']
        self.w3 = Web3(Web3.HTTPProvider(self.chain_config['rpc_url']))
        
        # Set up wallet
        self.private_key = private_key
        if not self.private_key.startswith('0x'):
            self.private_key = f"0x{self.private_key}"
            
        self.account = Account.from_key(self.private_key)
        self.logger = logger
        
        if logger:
            logger.info(f"Initialized wallet: {self.account.address}")
        else:
            print(f"Initialized wallet: {self.account.address}")
        
    def log(self, message, is_error=False):
        """Helper method to handle logging"""
        if self.logger:
            if is_error:
                self.logger.error(message)
            else:
                self.logger.info(message)
        else:
            print(message)

    def get_gas_price(self):
        """Get current gas price with a small buffer"""
        gas_price = self.w3.eth.gas_price
        return int(gas_price * 1.1)  # Add 10% buffer
        
    def distribute_hyb(self, to_address, amount):
        """
        Send HYB to a specific address
        to_address: The recipient address
        amount: Amount of HYB to send
        """
        try:
            # Convert address to checksum format
            to_address = Web3.to_checksum_address(to_address)
            
            # Convert HYB amount to Wei
            amount_in_wei = self.w3.to_wei(amount, 'ether')
            
            # Get the nonce for the transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Prepare transaction
            transaction = {
                'nonce': nonce,
                'to': to_address,
                'value': amount_in_wei,
                'gas': 50000,  # Increased gas limit for Hybrid network
                'maxFeePerGas': self.w3.eth.gas_price * 2,  # Double the current gas price
                'maxPriorityFeePerGas': self.w3.eth.gas_price,
                'chainId': self.chain_config['chain_id'],
                'type': 2  # EIP-1559 transaction type
            }
            
            # Estimate gas to make sure we have enough
            try:
                estimated_gas = self.w3.eth.estimate_gas(transaction)
                transaction['gas'] = int(estimated_gas * 1.2)  # Add 20% buffer to estimation
            except Exception as e:
                self.log(f"Gas estimation failed, using default: {str(e)}", True)
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            self.log(f"Sent {amount} HYB to {to_address}")
            self.log(f"Transaction hash: {tx_hash.hex()}")
            self.log(f"View on explorer: {self.chain_config['explorer']}/tx/{tx_hash.hex()}")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.log(f"Confirmed in block {receipt['blockNumber']}")
            self.log(f"Gas used: {receipt['gasUsed']}")
            
            return receipt
            
        except Exception as e:
            error_msg = f"Error sending to {to_address}: {str(e)}"
            self.log(error_msg, True)
            raise Exception(error_msg)

def main():
    # Load addresses from JSON files
    address_list = load_addresses(use_fallback=True)
    if not address_list:
        print("No addresses found in addresses.json or address_list.json")
        sys.exit(1)
    
    print(f"Loaded {len(address_list)} addresses")
    
    if len(sys.argv) == 1:  # No arguments provided, use defaults
        hyb_amount = DEFAULT_HYB_AMOUNT
        interval = DEFAULT_INTERVAL
        duration = None  # Infinite duration
    else:
        if len(sys.argv) != 4:
            print("Usage: python tx_scheduler.py [hyb_amount] [interval_minutes] [duration_minutes]")
            print("Or run without arguments for defaults:")
            print(f"- HYB Amount: {DEFAULT_HYB_AMOUNT}")
            print(f"- Interval: {DEFAULT_INTERVAL} minute(s)")
            print("- Duration: Infinite (until Ctrl+C)")
            sys.exit(1)
        
        hyb_amount = float(sys.argv[1])
        interval = int(sys.argv[2])
        duration = int(sys.argv[3])
    
    # Initialize and start the distributor
    distributor = HYBDistributor(
        address_list=address_list,
        token_amount=hyb_amount,
        time_interval=interval,
        duration_minutes=duration
    )
    
    distributor.start_distribution()

if __name__ == "__main__":
    main() 