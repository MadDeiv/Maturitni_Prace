# Import necessary libraries
import json
import hashlib
import time
import os
import ecdsa

# Block class represents a block in the blockchain
class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0, block_description="Block", merkle_root=None):
        # Initialize block attributes
        self.index = index  # Block's position in the chain
        self.timestamp = timestamp  # Time of block creation
        self.transactions = transactions  # List of Transaction objects
        self.previous_hash = previous_hash  # Hash of the previous block
        self.nonce = nonce  # Nonce for Proof of Work
        self.block_description = block_description  # Description of the block
        self.merkle_root = merkle_root if merkle_root else self.calculate_merkle_root()  # Merkle root of transactions

    def __hash__(self):
        # Calculate the block's hash (SHA-256)
        dict_copy = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root,
            "block_description": self.block_description,
        }
        block_data = json.dumps(dict_copy, sort_keys=True).encode()
        return hashlib.sha256(block_data).hexdigest()

    def proof_of_work(self, difficulty=4):
        # Perform Proof of Work to find a valid nonce
        self.nonce = 0
        target = "0" * difficulty  # Target hash starts with 'difficulty' zeros
        while not self.__hash__().startswith(target):
            self.nonce += 1
        return self.nonce

    def calculate_merkle_root(self):
        # Calculate the Merkle root of transactions
        tx_hashes = [hashlib.sha256(json.dumps(tx.to_dict(), sort_keys=True).encode()).hexdigest() 
                     for tx in self.transactions]
        if not tx_hashes:
            return hashlib.sha256("".encode()).hexdigest()  # Default hash for no transactions
        while len(tx_hashes) > 1:
            new_layer = []
            for i in range(0, len(tx_hashes), 2):
                left = tx_hashes[i]
                right = tx_hashes[i + 1] if i + 1 < len(tx_hashes) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                new_layer.append(combined)
            tx_hashes = new_layer
        return tx_hashes[0]

    def __str__(self):
        # String representation of the block for display
        transactions_str = "\n " + "\n ".join(map(str, self.transactions))
        return (f"Block Header\n"
                f"Description: {self.block_description}\n"
                f"Index: {self.index}\n"
                f"Timestamp: {self.timestamp}\n"
                f"Previous Hash: {self.previous_hash}\n"
                f"Merkle Root: {self.merkle_root}\n"
                f"Block Body\n"
                f"Transactions:{transactions_str}\n"
                f"Nonce: {self.nonce}")

# Transaction class represents a single transaction
class Transaction:
    def __init__(self, sender_pub_key, receiver_pub_key, amount, signature=None):
        # Initialize transaction attributes
        self.sender_pub_key = sender_pub_key  # Sender's public key
        self.receiver_pub_key = receiver_pub_key  # Receiver's public key
        self.amount = amount  # Transaction amount
        self.signature = signature  # Transaction signature (optional)

    def sign(self, private_key):
        # Sign the transaction with the sender's private key
        data = f"{self.sender_pub_key}{self.receiver_pub_key}{self.amount}"
        self.signature = private_key.sign(data.encode())

    def verify(self, public_key):
        # Verify the transaction signature with the sender's public key
        data = f"{self.sender_pub_key}{self.receiver_pub_key}{self.amount}"
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
        return vk.verify(self.signature, data.encode())

    def to_dict(self):
        # Convert transaction to a dictionary for serialization
        return {
            "sender": self.sender_pub_key,
            "receiver": self.receiver_pub_key,
            "amount": self.amount,
            "signature": self.signature.hex() if self.signature else None
        }

    def __str__(self):
        # String representation of the transaction
        return f"Sender: {self.sender_pub_key[:10]}..., Receiver: {self.receiver_pub_key[:10]}..., Amount: {self.amount}"

# Wallet class represents a user’s wallet
class Wallet:
    def __init__(self, name, balance=0, private_key=None, public_key=None):
        # Initialize wallet attributes
        self.name = name  # Wallet owner's name
        self.balance = balance  # Current balance
        if private_key:
            self.private_key = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
            self.public_key = self.private_key.get_verifying_key()
        else:
            self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
            self.public_key = self.private_key.get_verifying_key()

    def get_public_key(self):
        # Get the wallet's public key as a hex string
        return self.public_key.to_string().hex()

    def get_private_key(self):
        # Get the wallet's private key as a hex string
        return self.private_key.to_string().hex()

    def to_dict(self):
        # Convert wallet to a dictionary for serialization
        return {"name": self.name, "balance": self.balance, "public_key": self.get_public_key()}

    def __str__(self):
        # String representation of the wallet
        return f"Wallet: {self.name}, Public Key: {self.get_public_key()[:10]}..., Balance: {self.balance}"

# Blockchain class represents the cryptocurrency blockchain
class Blockchain:
    def __init__(self):
        # Initialize blockchain attributes
        self.block_list = []  # List of blocks
        self.wallets = {}  # Dictionary of wallets by public key
        self.pending_transactions = []  # List of unconfirmed transactions
        self.mining_reward = 50  # Reward for mining a block
        self.difficulty = 4  # PoW difficulty (number of leading zeros)
        self.directory = "prototype"  # Directory for saving files

    def genesis_block(self):
        # Create the genesis (first) block
        block = Block(0, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), [], "0", block_description="Genesis Block")
        block.proof_of_work(self.difficulty)
        self.block_list.append(block)

    def mine_block(self, miner_wallet):
        # Mine a new block with pending transactions and a mining reward
        reward_tx = Transaction("0", miner_wallet.get_public_key(), self.mining_reward)
        reward_tx.signature = b"mining_reward"  # Dummy signature for reward
        self.pending_transactions.append(reward_tx)

        last_block = self.block_list[-1]
        new_block = Block(len(self.block_list), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                          self.pending_transactions, last_block.__hash__())
        print(f"Mining block {new_block.index}...")
        new_block.proof_of_work(self.difficulty)
        self.block_list.append(new_block)
        print(f"Block {new_block.index} mined successfully!")
        miner_wallet.balance += self.mining_reward
        self.pending_transactions = []

    def add_transaction(self, sender_wallet, receiver_wallet, amount):
        # Add a transaction to the pending list
        if sender_wallet.balance < amount:
            return "Insufficient funds"
        tx = Transaction(sender_wallet.get_public_key(), receiver_wallet.get_public_key(), amount)
        tx.sign(sender_wallet.private_key)
        if not tx.verify(sender_wallet.get_public_key()):
            return "Invalid signature"
        sender_wallet.balance -= amount
        receiver_wallet.balance += amount
        self.pending_transactions.append(tx)
        return "Transaction added to pending list"

    def create_wallet(self, name):
        # Create a new wallet and add it to the blockchain
        wallet = Wallet(name)
        self.wallets[wallet.get_public_key()] = wallet
        return wallet

    def check_balance(self, public_key):
        # Check the balance of a wallet by public key
        return self.wallets[public_key].balance if public_key in self.wallets else "Wallet not found"

    def validate_blockchain(self):
        # Validate the blockchain's integrity
        for i in range(1, len(self.block_list)):
            current = self.block_list[i]
            prev = self.block_list[i - 1]
            if current.__hash__() != current.__hash__():  # Recalculate to ensure integrity
                return False
            if current.previous_hash != prev.__hash__():
                return False
            if current.__hash__()[:self.difficulty] != "0" * self.difficulty:
                return False
        return True

    def display_blockchain(self):
        # Return a string representation of the blockchain
        result = ""
        for block in self.block_list:
            result += str(block) + "\n\n"
        return result

    def save_blockchain_to_file(self):
        # Save the blockchain and wallets to a file
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        filename = os.path.join(self.directory, f"blockchain_{time.strftime('%Y%m%d%H%M%S', time.localtime())}.json")
        data = {
            "blocks": [block.__dict__ for block in self.block_list],
            "wallets": {pub_key: wallet.to_dict() for pub_key, wallet in self.wallets.items()}
        }
        with open(filename, "w") as file:
            json.dump(data, file, default=lambda x: x.to_dict() if isinstance(x, Transaction) else str(x), indent=4)
        self.save_wallets_private_keys(filename.replace("blockchain_", "wallets_"))
        return filename

    def load_blockchain_from_file(self, filename):
        # Load the blockchain and wallets from a file
        if not os.path.exists(filename):
            return f"File {filename} not found."
        
        with open(filename, "r") as file:
            data = json.load(file)

        self.block_list = []
        for block_data in data["blocks"]:
            transactions = [Transaction(tx["sender"], tx["receiver"], tx["amount"], 
                                        bytes.fromhex(tx["signature"]) if tx["signature"] else None)
                            for tx in block_data["transactions"]]
            block = Block(
                block_data["index"], block_data["timestamp"], transactions, block_data["previous_hash"],
                block_data["nonce"], block_data["block_description"], block_data["merkle_root"]
            )
            self.block_list.append(block)

        self.wallets = {}
        wallet_keys_file = filename.replace("blockchain_", "wallets_")
        if os.path.exists(wallet_keys_file):
            with open(wallet_keys_file, "r") as kf:
                key_data = json.load(kf)
            for pub_key, wallet_data in data["wallets"].items():
                private_key = key_data.get(pub_key, {}).get("private_key")
                self.wallets[pub_key] = Wallet(wallet_data["name"], wallet_data["balance"], private_key, pub_key)
        else:
            for pub_key, wallet_data in data["wallets"].items():
                self.wallets[pub_key] = Wallet(wallet_data["name"], wallet_data["balance"])

        if self.validate_blockchain():
            return f"Blockchain loaded successfully from {filename}"
        else:
            self.block_list = []
            self.wallets = {}
            self.genesis_block()
            return "Invalid blockchain loaded! Started new."

    def save_wallets_private_keys(self, filename):
        # Save wallet private keys to a separate file (for security)
        key_data = {pub_key: {"name": wallet.name, "private_key": wallet.get_private_key()}
                    for pub_key, wallet in self.wallets.items()}
        with open(filename, "w") as file:
            json.dump(key_data, file, indent=4)