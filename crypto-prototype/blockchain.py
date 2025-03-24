import json
import hashlib
import time
import os
import ecdsa  # Library for elliptic curve cryptography (ECDSA)

class Block:
    """Represents a block in the blockchain."""
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0, block_description="Block", merkle_root=None):
        """Initialize a block with its properties."""
        self.index = index  # Block number in the chain
        self.timestamp = timestamp  # Time of block creation
        self.transactions = transactions  # List of transactions in the block
        self.previous_hash = previous_hash  # Hash of the previous block
        self.nonce = nonce  # Number used for proof-of-work
        self.block_description = block_description  # Description of the block
        self.merkle_root = merkle_root if merkle_root else self.calculate_merkle_root()  # Root of the Merkle tree

    def __hash__(self):
        """Calculate the block’s hash based on its properties."""
        # Create a dictionary of block data, excluding transactions for simplicity
        dict_copy = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root,
            "block_description": self.block_description,
        }
        # Convert to JSON string and hash with SHA-256
        block_data = json.dumps(dict_copy, sort_keys=True).encode()
        return hashlib.sha256(block_data).hexdigest()

    def proof_of_work(self, difficulty=4):
        """Perform proof-of-work to find a valid nonce."""
        self.nonce = 0  # Start with nonce at 0
        target = "0" * difficulty  # Target hash starts with 'difficulty' zeros
        while not self.__hash__().startswith(target):  # Keep incrementing nonce until hash meets target
            self.nonce += 1
        return self.nonce  # Return the found nonce

    def calculate_merkle_root(self):
        """Calculate the Merkle root of the transactions."""
        # Hash each transaction
        tx_hashes = [hashlib.sha256(json.dumps(tx.to_dict(), sort_keys=True).encode()).hexdigest() 
                     for tx in self.transactions]
        if not tx_hashes:  # If no transactions, return hash of empty string
            return hashlib.sha256("".encode()).hexdigest()
        while len(tx_hashes) > 1:  # Build Merkle tree by pairing hashes
            new_layer = []
            for i in range(0, len(tx_hashes), 2):
                left = tx_hashes[i]
                right = tx_hashes[i + 1] if i + 1 < len(tx_hashes) else left  # Duplicate if odd number
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                new_layer.append(combined)
            tx_hashes = new_layer
        return tx_hashes[0]  # Return the root hash

    def __str__(self):
        """Return a string representation of the block."""
        transactions_str = "\n " + "\n ".join(map(str, self.transactions))  # Format transactions
        return (f"Description: {self.block_description}\n"
                f"Index: {self.index}\n"
                f"Timestamp: {self.timestamp}\n"
                f"Previous Hash: {self.previous_hash}\n"
                f"Hash: {self.__hash__()}\n"
                f"Nonce: {self.nonce}\n"
                f"Merkle Root: {self.merkle_root}\n"
                f"Transactions:{transactions_str}")

class Transaction:
    """Represents a transaction between wallets."""
    def __init__(self, sender_pub_key, receiver_pub_key, amount, signature=None):
        """Initialize a transaction with sender, receiver, amount, and optional signature."""
        self.sender_pub_key = sender_pub_key  # Sender’s public key
        self.receiver_pub_key = receiver_pub_key  # Receiver’s public key
        self.amount = amount  # Amount to transfer
        self.signature = signature if signature else None  # Digital signature (optional)

    def sign(self, private_key):
        """Sign the transaction with the sender’s private key."""
        data = f"{self.sender_pub_key}{self.receiver_pub_key}{self.amount}"  # Concatenate transaction data
        self.signature = private_key.sign(data.encode())  # Sign with ECDSA

    def verify(self, public_key):
        """Verify the transaction signature using the sender’s public key."""
        data = f"{self.sender_pub_key}{self.receiver_pub_key}{self.amount}"  # Recreate transaction data
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)  # Load public key
        return vk.verify(self.signature, data.encode())  # Verify signature

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
        return f"Sender: {self.sender_pub_key[:10]}..., Receiver: {self.receiver_pub_key[:10]}..., Amount: {self.amount}"

class Wallet:
    """Represents a user’s wallet with public and private keys."""
    def __init__(self, name, balance=0, private_key=None, public_key=None):
        """Initialize a wallet with a name, balance, and optional keys."""
        self.name = name  # Wallet owner’s name
        self.balance = balance  # Current balance
        if private_key:  # If private key is provided
            self.private_key = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
            self.public_key = self.private_key.get_verifying_key()  # Derive public key
        else:  # Generate new key pair if no private key provided
            self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
            self.public_key = self.private_key.get_verifying_key()

    def get_public_key(self):
        """Return the public key as a hexadecimal string."""
        return self.public_key.to_string().hex()

    def get_private_key(self):
        """Return the private key as a hexadecimal string."""
        return self.private_key.to_string().hex()

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
        self.block_list = []  # List of blocks
        self.wallets = {}  # Dictionary of wallets (public key -> Wallet object)
        self.pending_transactions = []  # List of unmined transactions
        self.mining_reward = 50  # Reward for mining a block
        self.difficulty = 4  # Proof-of-work difficulty (number of leading zeros)
        self.directory = "prototype"  # Directory for saving blockchain files

    def genesis_block(self):
        """Create the first (genesis) block in the blockchain."""
        block = Block(0, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), [], "0", 
                      block_description="Genesis Block")
        block.proof_of_work(self.difficulty)  # Mine the genesis block
        self.block_list.append(block)

    def mine_block(self, miner_pub_key):
        """Mine a new block and reward the miner."""
        # Add a mining reward transaction
        reward_tx = Transaction("0", miner_pub_key, self.mining_reward)
        reward_tx.signature = b"mining_reward"  # Dummy signature for reward transaction
        self.pending_transactions.append(reward_tx)

        last_block = self.block_list[-1]  # Get the last block
        # Create a new block with pending transactions
        new_block = Block(len(self.block_list), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                          self.pending_transactions, last_block.__hash__())
        print(f"Mining block {new_block.index}...")  # Log mining start
        new_block.proof_of_work(self.difficulty)  # Perform proof-of-work
        self.block_list.append(new_block)  # Add the mined block
        print(f"Block {new_block.index} mined successfully!")  # Log success
        if miner_pub_key in self.wallets:  # Update miner’s balance
            self.wallets[miner_pub_key].balance += self.mining_reward
        self.pending_transactions = []  # Clear pending transactions

    def add_transaction(self, sender_pub_key, receiver_pub_key, amount, private_key):
        """Add a transaction to the pending list after validation."""
        # Check if sender and receiver exist
        if sender_pub_key not in self.wallets or receiver_pub_key not in self.wallets:
            return "Invalid sender or receiver public key"
        if self.wallets[sender_pub_key].balance < amount:  # Check funds
            return "Insufficient funds"
        
        tx = Transaction(sender_pub_key, receiver_pub_key, amount)  # Create transaction
        # Load and validate the private key
        sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
        if sk.get_verifying_key().to_string().hex() != sender_pub_key:  # Verify key match
            return "Private key does not match sender’s public key"
        
        tx.sign(sk)  # Sign the transaction
        if not tx.verify(sender_pub_key):  # Verify the signature
            return "Invalid signature"
        
        # Update balances and add to pending transactions
        self.wallets[sender_pub_key].balance -= amount
        self.wallets[receiver_pub_key].balance += amount
        self.pending_transactions.append(tx)
        return "Transaction added to pending list"

    def create_wallet(self, name):
        """Create a new wallet and store it without the private key."""
        wallet = Wallet(name)  # Create a new wallet with keys
        pub_key = wallet.get_public_key()  # Get the public key
        # Store a wallet copy without private key in the blockchain
        self.wallets[pub_key] = Wallet(name, 0, public_key=pub_key)
        return wallet  # Return the full wallet for private key display

    def check_balance(self, public_key):
        """Return the balance of a wallet by public key."""
        return self.wallets[public_key].balance if public_key in self.wallets else "Wallet not found"

    def validate_blockchain(self):
        """Validate the integrity of the blockchain."""
        for i in range(1, len(self.block_list)):  # Check each block after genesis
            current = self.block_list[i]
            prev = self.block_list[i - 1]
            if current.__hash__() != current.__hash__():  # Should be consistent (redundant check)
                return False
            if current.previous_hash != prev.__hash__():  # Check chain linkage
                return False
            if current.__hash__()[:self.difficulty] != "0" * self.difficulty:  # Check proof-of-work
                return False
        return True

    def display_blockchain(self):
        """Return a string representation of the entire blockchain."""
        result = ""
        for block in self.block_list:
            result += str(block) + "\n\n"  # Concatenate block strings
        return result

    def save_blockchain_to_file(self):
        """Save the blockchain state to a JSON file."""
        if not os.path.exists(self.directory):  # Create directory if it doesn’t exist
            os.makedirs(self.directory)
        # Generate a timestamped filename
        filename = os.path.join(self.directory, f"blockchain_{time.strftime('%Y%m%d%H%M%S', time.localtime())}.json")
        # Prepare data for serialization
        data = {
            "blocks": [block.__dict__ for block in self.block_list],
            "wallets": {pub_key: wallet.to_dict() for pub_key, wallet in self.wallets.items()}
        }
        with open(filename, "w") as file:  # Write to file
            json.dump(data, file, default=lambda x: x.to_dict() if isinstance(x, Transaction) else str(x), indent=4)
        return filename

    def load_blockchain_from_file(self, filename):
        """Load a blockchain state from a JSON file."""
        if not os.path.exists(filename):  # Check if file exists
            return f"File {filename} not found."
        
        with open(filename, "r") as file:  # Read the file
            data = json.load(file)

        self.block_list = []  # Clear current blockchain
        # Reconstruct blocks
        for block_data in data["blocks"]:
            transactions = [Transaction(tx["sender"], tx["receiver"], tx["amount"], 
                                        bytes.fromhex(tx["signature"]) if tx["signature"] else None)
                            for tx in block_data["transactions"]]
            block = Block(
                block_data["index"], block_data["timestamp"], transactions, block_data["previous_hash"],
                block_data["nonce"], block_data["block_description"], block_data["merkle_root"]
            )
            self.block_list.append(block)

        self.wallets = {}  # Clear current wallets
        # Reconstruct wallets
        for pub_key, wallet_data in data["wallets"].items():
            self.wallets[pub_key] = Wallet(wallet_data["name"], wallet_data["balance"], public_key=pub_key)

        if self.validate_blockchain():  # Validate loaded blockchain
            return f"Blockchain loaded successfully from {filename}"
        else:  # If invalid, reset to genesis state
            self.block_list = []
            self.wallets = {}
            self.genesis_block()
            return "Invalid blockchain loaded! Started new."