from flask import Flask, render_template, request, redirect, url_for, flash
from blockchain import Blockchain  # Import the Blockchain class from blockchain.py

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = "crypto_prototype_secret"  # Secret key for session security (e.g., flash messages)

# Create a global Blockchain instance to manage the cryptocurrency
blockchain = Blockchain()

@app.route('/')
def index():
    """Render the home page with blockchain and wallet details."""
    return render_template('index.html', blockchain=blockchain.display_blockchain(), 
                           wallets=blockchain.wallets)

@app.route('/create_wallet', methods=['GET', 'POST'])
def create_wallet():
    """Handle wallet creation and redirect to show the private key."""
    if request.method == 'POST':
        name = request.form['name'].strip()
        if name:
            wallet = blockchain.create_wallet(name)  # Create a single wallet
            flash(f"Wallet '{name}' created successfully!", "success")
            return redirect(url_for('show_private_key', public_key=wallet.get_public_key(), 
                                    private_key=wallet.get_private_key()))
        flash("Please enter a name.", "error")
    return render_template('create_wallet.html')

@app.route('/show_private_key/<public_key>/<private_key>')
def show_private_key(public_key, private_key):
    """Display the wallet details and private key after creation."""
    if public_key in blockchain.wallets:
        wallet = blockchain.wallets[public_key]
        return render_template('show_private_key.html', wallet=wallet, private_key=private_key)
    flash("Wallet not found.", "error")
    return redirect(url_for('index'))

@app.route('/check_balance', methods=['GET', 'POST'])
def check_balance():
    """Check and display the balance of a wallet by public key."""
    if request.method == 'POST':
        public_key = request.form['public_key'].strip()  # Remove whitespace
        balance = blockchain.check_balance(public_key)
        print(f"Checking balance for: {public_key}")  # Debug
        if isinstance(balance, str):
            flash(balance, "error")
        else:
            flash(f"Balance for {public_key[:10]}...: {balance}", "success")
        return redirect(url_for('index'))
    return render_template('check_balance.html')

@app.route('/send_transaction', methods=['GET', 'POST'])
def send_transaction():
    """Handle sending a transaction with manual private key input."""
    if request.method == 'POST':
        sender_pub = request.form['sender_pub'].strip()
        private_key = request.form['private_key'].strip()
        receiver_pub = request.form['receiver_pub'].strip()
        try:
            amount = float(request.form['amount'])
            result = blockchain.add_transaction(sender_pub, receiver_pub, amount, private_key)
            flash(result, "success" if "added" in result.lower() else "error")
        except ValueError:
            flash("Invalid amount entered.", "error")
        return redirect(url_for('index'))
    return render_template('send_transaction.html', wallets=blockchain.wallets)

@app.route('/mine_block', methods=['GET', 'POST'])
def mine_block():
    """Mine a new block and reward the miner."""
    if request.method == 'POST':
        miner_pub = request.form['miner_pub'].strip()
        if miner_pub in blockchain.wallets:
            blockchain.mine_block(miner_pub)
            flash(f"Block mined by {blockchain.wallets[miner_pub].name}!", "success")
        else:
            flash("Invalid miner public key.", "error")
        return redirect(url_for('index'))
    return render_template('mine_block.html', wallets=blockchain.wallets)

@app.route('/save_blockchain', methods=['POST'])
def save_blockchain():
    """Save the current blockchain state to a file."""
    filename = blockchain.save_blockchain_to_file()
    flash(f"Blockchain saved to {filename}", "success")
    return redirect(url_for('index'))

@app.route('/load_blockchain', methods=['GET', 'POST'])
def load_blockchain():
    """Load a blockchain state from a file."""
    if request.method == 'POST':
        filename = request.form['filename'].strip()
        result = blockchain.load_blockchain_from_file(filename)
        flash(result, "success" if "successfully" in result.lower() else "error")
        return redirect(url_for('index'))
    return render_template('load_blockchain.html')

if __name__ == '__main__':
    """Entry point for running the application."""
    blockchain.genesis_block()  # Create the genesis block when the app starts
    app.run(debug=True)  # Run the Flask app in debug mode on localhost:5000