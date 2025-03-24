import json
import hashlib
import time
import os
import ecdsa

class Block:
    """Represents a block in the blockchain."""
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0, block_description="Block", merkle_root=None):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.block_description = block_description
        self.merkle_root = merkle_root if merkle_root else self.calculate_merkle_root()

    def __hash__(self):
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
        self.nonce = 0
        target = "0" * difficulty
        while not self.__hash__().startswith(target):
            self.nonce += 1
        return self.nonce

    def calculate_merkle_root(self):
        tx_hashes = [hashlib.sha256(json.dumps(tx.to_dict(), sort_keys=True).encode()).hexdigest() 
                     for tx in self.transactions]
        if not tx_hashes:
            return hashlib.sha256("".encode()).hexdigest()
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
        transactions_str = "\n " + "\n ".join(map(str, self.transactions))
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
        self.sender_pub_key = sender_pub_key
        self.receiver_pub_key = receiver_pub_key
        self.amount = amount
        self.signature = signature if signature else None

    def sign(self, private_key):
        data = f"{self.sender_pub_key}{self.receiver_pub_key}{self.amount}"
        self.signature = private_key.sign(data.encode())

    def verify(self, public_key):
        data = f"{self.sender_pub_key}{self.receiver_pub_key}{self.amount}"
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
        return vk.verify(self.signature, data.encode())

    def to_dict(self):
        return {
            "sender": self.sender_pub_key,
            "receiver": self.receiver_pub_key,
            "amount": self.amount,
            "signature": self.signature.hex() if self.signature else None
        }

    def __str__(self):
        return f"Sender: {self.sender_pub_key[:10]}..., Receiver: {self.receiver_pub_key[:10]}..., Amount: {self.amount}"

class Wallet:
    """Represents a user’s wallet with public and private keys."""
    def __init__(self, name, balance=0, private_key=None, public_key=None):
        self.name = name
        self.balance = balance
        if private_key:
            self.private_key = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
            self.public_key = self.private_key.get_verifying_key()
        else:
            self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
            self.public_key = self.private_key.get_verifying_key()

    def get_public_key(self):
        return self.public_key.to_string().hex()

    def get_private_key(self):
        return self.private_key.to_string().hex()

    def to_dict(self):
        return {"name": self.name, "balance": self.balance, "public_key": self.get_public_key()}

    def __str__(self):
        return f"Wallet: {self.name}, Public Key: {self.get_public_key()[:10]}..., Balance: {self.balance}"

class Blockchain:
    """Manages the blockchain, wallets, and transactions."""
    def __init__(self):
        self.block_list = []
        self.wallets = {}
        self.pending_transactions = []
        self.mining_reward = 50
        self.difficulty = 4
        self.directory = "prototype"

    def genesis_block(self):
        block = Block(0, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), [], "0", 
                      block_description="Genesis Block")
        block.proof_of_work(self.difficulty)
        self.block_list.append(block)

    def mine_block(self, miner_pub_key):
        reward_tx = Transaction("0", miner_pub_key, self.mining_reward)
        reward_tx.signature = b"mining_reward"
        self.pending_transactions.append(reward_tx)

        last_block = self.block_list[-1]
        new_block = Block(len(self.block_list), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                          self.pending_transactions, last_block.__hash__())
        print(f"Mining block {new_block.index}...")
        new_block.proof_of_work(self.difficulty)
        self.block_list.append(new_block)
        print(f"Block {new_block.index} mined successfully!")
        if miner_pub_key in self.wallets:
            self.wallets[miner_pub_key].balance += self.mining_reward
        self.pending_transactions = []

    def add_transaction(self, sender_pub_key, receiver_pub_key, amount, private_key):
        if sender_pub_key not in self.wallets or receiver_pub_key not in self.wallets:
            return "Invalid sender or receiver public key"
        if self.wallets[sender_pub_key].balance < amount:
            return "Insufficient funds"
        
        tx = Transaction(sender_pub_key, receiver_pub_key, amount)
        try:
            sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
            if sk.get_verifying_key().to_string().hex() != sender_pub_key:
                return "Private key does not match sender’s public key"
            tx.sign(sk)
            if not tx.verify(sender_pub_key):
                return "Invalid signature"
        except ValueError:
            return "Invalid private key format"
        
        self.wallets[sender_pub_key].balance -= amount
        self.wallets[receiver_pub_key].balance += amount
        self.pending_transactions.append(tx)
        return "Transaction added to pending list"

    def create_wallet(self, name):
        """Create a new wallet and store it without duplicating."""
        wallet = Wallet(name)  # Create one wallet instance
        pub_key = wallet.get_public_key()
        self.wallets[pub_key] = wallet  # Store the same instance directly
        print(f"Created wallet: {name}, Public Key: {pub_key}")  # Debug
        return wallet

    def check_balance(self, public_key):
        """Return the balance of a wallet by public key."""
        print(f"Checking balance for: {public_key}")  # Debug
        print(f"Available wallets: {list(self.wallets.keys())}")  # Debug
        return self.wallets[public_key].balance if public_key in self.wallets else "Wallet not found"

    def validate_blockchain(self):
        for i in range(1, len(self.block_list)):
            current = self.block_list[i]
            prev = self.block_list[i - 1]
            if current.previous_hash != prev.__hash__():
                return False
            if current.__hash__()[:self.difficulty] != "0" * self.difficulty:
                return False
        return True

    def display_blockchain(self):
        if not self.block_list:
            return "Blockchain is empty."
        result = ""
        for block in self.block_list:
            result += str(block) + "\n\n"
        return result.strip()

    def save_blockchain_to_file(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        filename = os.path.join(self.directory, f"blockchain_{time.strftime('%Y%m%d%H%M%S', time.localtime())}.json")
        data = {
            "blocks": [block.__dict__ for block in self.block_list],
            "wallets": {pub_key: wallet.to_dict() for pub_key, wallet in self.wallets.items()}
        }
        with open(filename, "w") as file:
            json.dump(data, file, default=lambda x: x.to_dict() if isinstance(x, Transaction) else str(x), indent=4)
        return filename

    def load_blockchain_from_file(self, filename):
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
        for pub_key, wallet_data in data["wallets"].items():
            self.wallets[pub_key] = Wallet(wallet_data["name"], wallet_data["balance"], public_key=pub_key)

        if self.validate_blockchain():
            return f"Blockchain loaded successfully from {filename}"
        else:
            self.block_list = []
            self.wallets = {}
            self.genesis_block()
            return "Invalid blockchain loaded! Started new."