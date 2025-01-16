import eventlet
eventlet.monkey_patch()

import os
import random
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from tx_scheduler import HYBDistributor, load_addresses, save_addresses
from dotenv import load_dotenv
import threading
import queue
import logging
import time
import webbrowser

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Global variables
distributor_thread = None
stop_event = None
web_logger = None
log_queue = queue.Queue()

class WebLogger:
    def __init__(self):
        self.app = app

    def info(self, msg):
        with self.app.app_context():
            log_queue.put({"type": "info", "message": msg})
            socketio.emit('log_message', {"type": "info", "message": msg})
            logger.info(msg)
        
    def error(self, msg):
        with self.app.app_context():
            log_queue.put({"type": "error", "message": msg})
            socketio.emit('log_message', {"type": "error", "message": msg})
            logger.error(msg)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_distribution')
def handle_start_distribution(data):
    global distributor_thread
    global stop_event
    global web_logger

    if distributor_thread and distributor_thread.is_alive():
        return {'status': 'error', 'message': 'Distribution is already running'}

    # Initialize logger first
    stop_event = threading.Event()
    web_logger = WebLogger()

    # Get private key from input or .env file
    private_key = data.get('private_key', '').strip()
    if not private_key:
        private_key = os.getenv('PRIVATE_KEY', '').strip()
        if not private_key:
            web_logger.error("No private key provided and none found in .env file")
            return {'status': 'error', 'message': 'No private key provided and none found in .env file. Please either enter a private key or add it to the .env file.'}
        web_logger.info("Using private key from .env file")
    
    # Validate private key format
    if not private_key.startswith('0x'):
        private_key = f"0x{private_key}"
    
    # Validate private key length (should be 66 characters including 0x prefix for a valid private key)
    if len(private_key) != 66:
        web_logger.error("Invalid private key length. Private key should be 64 characters (32 bytes) plus '0x' prefix")
        return {'status': 'error', 'message': 'Invalid private key length. Private key should be 64 characters (32 bytes) plus 0x prefix'}

    try:
        # Validate private key by attempting to create an account
        from eth_account import Account
        Account.from_key(private_key)
    except Exception as e:
        web_logger.error(f"Invalid private key format: {str(e)}")
        return {'status': 'error', 'message': f'Invalid private key format: {str(e)}'}

    hyb_amount = data.get('hyb_amount')
    interval = data.get('interval')
    addresses = data.get('addresses', [])
    recipient_settings = data.get('recipient_settings', {})

    # If no addresses provided in web UI, use addresses from address_list.json
    if not addresses:
        addresses = load_addresses(use_fallback=True)
        if not addresses:
            return {'status': 'error', 'message': 'No addresses provided and no fallback addresses found in address_list.json'}
        web_logger.info(f"Using {len(addresses)} addresses from address_list.json")

    def distribution_task():
        with app.app_context():
            try:
                distributor = HYBDistributor(private_key, web_logger)
                while not stop_event.is_set():
                    try:
                        # Get fresh random values for this round
                        if isinstance(hyb_amount, list):
                            current_amount = random.uniform(hyb_amount[0], hyb_amount[1])
                            web_logger.info(f"Generated random amount for this round: {current_amount} HYB")
                        else:
                            current_amount = hyb_amount

                        if isinstance(interval, list):
                            current_interval = random.randint(interval[0], interval[1])
                            web_logger.info(f"Generated random interval for this round: {current_interval} minutes")
                        else:
                            current_interval = interval

                        # Get fresh random recipients for this round
                        if recipient_settings.get('useRandom'):
                            count = recipient_settings.get('count', 1)
                            always_include = recipient_settings.get('alwaysIncludeAddress')
                            
                            # First, handle the always-include address if provided
                            if always_include:
                                try:
                                    # Generate a new random amount for this transaction if enabled
                                    if isinstance(hyb_amount, list):
                                        tx_amount = random.uniform(hyb_amount[0], hyb_amount[1])
                                        web_logger.info(f"Generated random amount for always-include address: {tx_amount} HYB")
                                    else:
                                        tx_amount = current_amount

                                    # Send to always-include address first
                                    web_logger.info(f"Sending to always-include address: {always_include}")
                                    distributor.distribute_hyb(always_include, tx_amount)
                                except Exception as e:
                                    web_logger.error(f"Failed to distribute to always-include address {always_include}: {str(e)}")

                            # Remove always-include address from the pool
                            selection_pool = [addr for addr in addresses if addr != always_include]
                            
                            # Select random addresses for the remaining transactions
                            if selection_pool:
                                random_selection = random.sample(selection_pool, min(count, len(selection_pool)))
                                web_logger.info(f"Selected {len(random_selection)} additional random recipients for this round")
                                
                                # Send to random selections
                                for address in random_selection:
                                    if stop_event.is_set():
                                        break
                                    try:
                                        # Generate a new random amount for each transaction if enabled
                                        if isinstance(hyb_amount, list):
                                            tx_amount = random.uniform(hyb_amount[0], hyb_amount[1])
                                            web_logger.info(f"Generated random amount for this transaction: {tx_amount} HYB")
                                        else:
                                            tx_amount = current_amount

                                        distributor.distribute_hyb(address, tx_amount)
                                    except Exception as e:
                                        web_logger.error(f"Failed to distribute to {address}: {str(e)}")
                        else:
                            # If not using random selection, send to all addresses
                            for address in addresses:
                                if stop_event.is_set():
                                    break
                                try:
                                    # Generate a new random amount for each transaction if enabled
                                    if isinstance(hyb_amount, list):
                                        tx_amount = random.uniform(hyb_amount[0], hyb_amount[1])
                                        web_logger.info(f"Generated random amount for this transaction: {tx_amount} HYB")
                                    else:
                                        tx_amount = current_amount

                                    distributor.distribute_hyb(address, tx_amount)
                                except Exception as e:
                                    web_logger.error(f"Failed to distribute to {address}: {str(e)}")

                        if stop_event.is_set():
                            break

                        # Wait for the interval
                        web_logger.info(f"Waiting {current_interval} minutes until next distribution...")
                        for _ in range(current_interval * 60):
                            if stop_event.is_set():
                                break
                            eventlet.sleep(1)

                    except Exception as e:
                        web_logger.error(f"Error in distribution loop: {str(e)}")
                        eventlet.sleep(5)  # Wait before retrying

            except Exception as e:
                web_logger.error(f"Distribution error: {str(e)}")
            finally:
                socketio.emit('distribution_stopped')

    distributor_thread = threading.Thread(target=distribution_task)
    distributor_thread.daemon = True
    distributor_thread.start()
    return {'status': 'success', 'message': 'Distribution started'}

@socketio.on('stop_distribution')
def handle_stop_distribution():
    global stop_event
    
    if not stop_event:
        return {'status': 'error', 'message': 'Distribution is not running'}
    
    try:
        stop_event.set()
        return {'status': 'success', 'message': 'Distribution stopping...'}
    except Exception as e:
        web_logger.error(f"Failed to stop distribution: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def open_browser():
    webbrowser.open('http://localhost:5000')

def main():
    try:
        # Check if templates/index.html exists
        if not os.path.exists('templates/index.html'):
            logger.error("templates/index.html not found. Please ensure the file exists in the templates directory.")
            print("\nError: templates/index.html not found")
            print("Please ensure:")
            print("1. The 'templates' directory exists")
            print("2. 'index.html' is present in the templates directory")
            input("\nPress Enter to exit...")  # Keep console open
            return

        # Start the web server
        logger.info("Starting web server...")
        print("Opening web interface in your default browser...")
        # Open browser after a short delay to ensure server is running
        threading.Timer(1.5, open_browser).start()
        socketio.run(app, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error starting web server: {str(e)}")
        print("\nAn error occurred:")
        print(str(e))
        print("\nCheck if:")
        print("1. Port 5000 is not in use")
        print("2. All required packages are installed")
        print("3. templates/index.html exists")
        print("\nTry running: pip install -r requirements.txt")
        input("\nPress Enter to exit...")  # Keep console open

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("\nFatal error occurred:")
        print(str(e))
        input("\nPress Enter to exit...")  # Keep console open