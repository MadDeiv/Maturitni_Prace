import json  # For JSON serialization/deserialization
import hashlib  # For SHA-256 hashing
import time  # For timestamps
import os  # For file operations
import ecdsa  # Library for elliptic curve cryptography (ECDSA)

class Block:
    """Represents a block in the blockchain."""
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0, block_description="Block"):
        """Initialize a block with its properties."""
        self.index = index  # Block number in the chain (starts at 0 for genesis)
        self.timestamp = timestamp  # Time of block creation
        self.transactions = transactions  # List of Transaction objects in the block
        self.previous_hash = previous_hash  # Hash of the previous block for chain integrity
        self.nonce = nonce  # Number used once for proof-of-work
        self.block_description = block_description  # Descriptive label for the block


    def __hash__(self):
        """Calculate the block’s hash based on its properties."""
        # Create a dictionary of block data (excluding transactions for simplicity)
        dict_copy = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,

            "block_description": self.block_description,
        }
        # Convert to JSON string, sort keys for consistency, encode to bytes, and hash with SHA-256
        block_data = json.dumps(dict_copy, sort_keys=True).encode()
        return hashlib.sha256(block_data).hexdigest()  # Return the hash as a hex string

    def proof_of_work(self, difficulty=4):
        """Perform proof-of-work to find a valid nonce."""
        self.nonce = 0  # Start with nonce at 0
        target = "0" * difficulty  # Target hash must start with 'difficulty' zeros
        while not self.__hash__().startswith(target):  # Loop until hash meets the target
            self.nonce += 1  # Increment nonce to change the hash
        return self.nonce  # Return the nonce that satisfies the condition



    def __str__(self):
        """Return a string representation of the block for display."""
        transactions_str = "\n " + "\n ".join(map(str, self.transactions))  # Format transactions with newlines
        return (f"Description: {self.block_description}\n"
                f"Index: {self.index}\n"
                f"Timestamp: {self.timestamp}\n"
                f"Previous Hash: {self.previous_hash}\n"
                f"Hash: {self.__hash__()}\n"
                f"Nonce: {self.nonce}\n"

                f"Transactions:{transactions_str}")

class Transaction:
    """Represents a transaction between wallets."""
    def __init__(self, sender_pub_key, receiver_pub_key, amount, signature=None):
        """Initialize a transaction with sender, receiver, amount, and optional signature."""
        self.sender_pub_key = sender_pub_key  # Sender’s public key (hex string)
        self.receiver_pub_key = receiver_pub_key  # Receiver’s public key (hex string)
        self.amount = amount  # Amount of cryptocurrency to transfer
        self.signature = signature if signature else None  # Digital signature (bytes or None)

    def sign(self, private_key):
        """Sign the transaction with the sender’s private key."""
        # Concatenate sender, receiver, and amount for signing
        data = f"{self.sender_pub_key}{self.receiver_pub_key}{self.amount}"
        self.signature = private_key.sign(data.encode())  # Sign using ECDSA and store as bytes

    def verify(self, public_key):
        """Verify the transaction signature using the sender’s public key."""
        # Recreate the data string that was signed
        data = f"{self.sender_pub_key}{self.receiver_pub_key}{self.amount}"
        # Load the public key from its hex string
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
        return vk.verify(self.signature, data.encode())  # Return True if signature is valid

    def to_dict(self):
        """Convert transaction to a dictionary for serialization."""
        return {
            "sender": self.sender_pub_key,
            "receiver": self.receiver_pub_key,
            "amount": self.amount,
            "signature": self.signature.hex() if self.signature else None  # Convert signature to hex
        }

    def __str__(self):
        """Return a string representation of the transaction."""
        # Show truncated public keys for readability
        return f"Sender: {self.sender_pub_key[:10]}..., Receiver: {self.receiver_pub_key[:10]}..., Amount: {self.amount}"

class Wallet:
    """Represents a user’s wallet with public and private keys."""
    def __init__(self, name, balance=0, private_key=None, public_key=None):
        """Initialize a wallet with a name, balance, and optional keys."""
        self.name = name  # Wallet owner’s name
        self.balance = balance  # Current balance in cryptocurrency units
        if private_key:  # If a private key is provided
            # Load the private key from hex and derive the public key
            self.private_key = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
            self.public_key = self.private_key.get_verifying_key()
        else:  # If no private key, generate a new key pair
            self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
            self.public_key = self.private_key.get_verifying_key()

    def get_public_key(self):
        """Return the public key as a hexadecimal string."""
        return self.public_key.to_string().hex()  # Convert public key to hex format

    def get_private_key(self):
        """Return the private key as a hexadecimal string."""
        return self.private_key.to_string().hex()  # Convert private key to hex format

    def to_dict(self):
        """Convert wallet to a dictionary for serialization (excludes private key)."""
        return {"name": self.name, "balance": self.balance, "public_key": self.get_public_key()}

    def __str__(self):
        """Return a string representation of the wallet."""
        return f"Wallet: {self.name}, Public Key: {self.get_public_key()[:10]}..., Balance: {self.balance}"

class Blockchain:
    """Manages the blockchain, wallets, and transactions."""
    def __init__(self):
        """Initialize the blockchain with empty lists and default settings."""
        self.block_list = []  # List to store all blocks
        self.wallets = {}  # Dictionary mapping public keys to Wallet objects
        self.pending_transactions = []  # List of transactions waiting to be mined
        self.mining_reward = 50  # Reward given to miners for each block (in units)
        self.difficulty = 4  # Number of leading zeros required for proof-of-work
        self.directory = "prototype"  # Directory where blockchain files are saved

    def genesis_block(self):
        """Create the first (genesis) block in the blockchain."""
        # Create a block with index 0, no transactions, and previous hash "0"
        block = Block(0, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), [], "0", 
                      block_description="Genesis Block")
        block.proof_of_work(self.difficulty)  # Mine the block to set the nonce
        self.block_list.append(block)  # Add the genesis block to the chain

    def mine_block(self, miner_pub_key):
        """Mine a new block and reward the miner."""
        # Create a reward transaction from "0" (system) to the miner
        reward_tx = Transaction("0", miner_pub_key, self.mining_reward)
        reward_tx.signature = b"mining_reward"  # Use a dummy signature for the reward
        self.pending_transactions.append(reward_tx)  # Add reward to pending transactions

        last_block = self.block_list[-1]  # Get the most recent block
        # Create a new block with the next index and current timestamp
        new_block = Block(len(self.block_list), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                          self.pending_transactions, last_block.__hash__())
        print(f"Mining block {new_block.index}...")  # Log mining start
        new_block.proof_of_work(self.difficulty)  # Perform proof-of-work
        self.block_list.append(new_block)  # Add the mined block to the chain
        print(f"Block {new_block.index} mined successfully!")  # Log success
        if miner_pub_key in self.wallets:  # If miner exists, update their balance
            self.wallets[miner_pub_key].balance += self.mining_reward
        self.pending_transactions = []  # Clear the pending transactions list

    def add_transaction(self, sender_pub_key, receiver_pub_key, amount, private_key):
        """Add a transaction to the pending list after validation."""
        # Check if both sender and receiver wallets exist
        if sender_pub_key not in self.wallets or receiver_pub_key not in self.wallets:
            return "Invalid sender or receiver public key"
        if self.wallets[sender_pub_key].balance < amount:  # Check sender’s funds
            return "Insufficient funds"
        
        tx = Transaction(sender_pub_key, receiver_pub_key, amount)  # Create a new transaction
        try:
            # Load the private key and verify it matches the sender’s public key
            sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
            if sk.get_verifying_key().to_string().hex() != sender_pub_key:
                return "Private key does not match sender’s public key"
            tx.sign(sk)  # Sign the transaction with the private key
            if not tx.verify(sender_pub_key):  # Verify the signature
                return "Invalid signature"
        except ValueError:  # Handle invalid private key format
            return "Invalid private key format"
        
        # Update wallet balances and add transaction to pending list
        self.wallets[sender_pub_key].balance -= amount
        self.wallets[receiver_pub_key].balance += amount
        self.pending_transactions.append(tx)
        return "Transaction added to pending list"  # Indicate success

    def create_wallet(self, name):
        """Create a new wallet and store it without duplicating."""
        wallet = Wallet(name)  # Create a single wallet instance with a new key pair
        pub_key = wallet.get_public_key()  # Get the public key as a hex string
        self.wallets[pub_key] = wallet  # Store the wallet in the dictionary using its public key
        print(f"Created wallet: {name}, Public Key: {pub_key}")  # Debug: log wallet creation
        return wallet  # Return the wallet object for immediate use

    def check_balance(self, public_key):
        """Return the balance of a wallet by public key."""
        print(f"Checking balance for: {public_key}")  # Debug: log the key being checked
        print(f"Available wallets: {list(self.wallets.keys())}")  # Debug: log all stored keys
        # Return balance if wallet exists, otherwise an error message
        return self.wallets[public_key].balance if public_key in self.wallets else "Wallet not found"

    def display_blockchain(self):
        """Return a string representation of the entire blockchain."""
        if not self.block_list:  # Handle empty blockchain case
            return "Blockchain is empty."
        result = ""  # Build the display string
        for block in self.block_list:
            result += str(block) + "\n\n"  # Add each block’s string with spacing
        return result.strip()  # Remove trailing newlines

    def save_blockchain_to_file(self):
        """Save the blockchain state to a JSON file."""
        if not os.path.exists(self.directory):  # Create the directory if it doesn’t exist
            os.makedirs(self.directory)
        # Generate a unique filename with a timestamp
        filename = os.path.join(self.directory, f"blockchain_{time.strftime('%Y%m%d%H%M%S', time.localtime())}.json")
        # Prepare data for serialization
        data = {
            "blocks": [block.__dict__ for block in self.block_list],  # Convert blocks to dictionaries
            "wallets": {pub_key: wallet.to_dict() for pub_key, wallet in self.wallets.items()}  # Convert wallets
        }
        with open(filename, "w") as file:  # Write data to the file
            # Use a custom serializer for Transaction objects
            json.dump(data, file, default=lambda x: x.to_dict() if isinstance(x, Transaction) else str(x), indent=4)
        return filename  # Return the saved file’s path

    def load_blockchain_from_file(self, filename):
        """Load a blockchain state from a JSON file."""
        if not os.path.exists(filename):  # Check if the file exists
            return f"File {filename} not found."
        
        with open(filename, "r") as file:  # Read the JSON file
            data = json.load(file)

        self.block_list = []  # Clear the current blockchain
        # Reconstruct blocks from the file data
        for block_data in data["blocks"]:
            # Rebuild transactions list
            transactions = [Transaction(tx["sender"], tx["receiver"], tx["amount"], 
                                        bytes.fromhex(tx["signature"]) if tx["signature"] else None)
                            for tx in block_data["transactions"]]
            # Create a new Block object with loaded data
            block = Block(
                block_data["index"], block_data["timestamp"], transactions, block_data["previous_hash"],
                block_data["nonce"], block_data["block_description"]
            )
            self.block_list.append(block)  # Add to the blockchain

        self.wallets = {}  # Clear current wallets
        # Reconstruct wallets from the file data
        for pub_key, wallet_data in data["wallets"].items():
            self.wallets[pub_key] = Wallet(wallet_data["name"], wallet_data["balance"], public_key=pub_key)

        return f"Blockchain loaded successfully from {filename}"
