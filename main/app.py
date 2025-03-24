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
    # Display the blockchain and list of wallets using the index.html template
    return render_template('index.html', blockchain=blockchain.display_blockchain(), 
                           wallets=blockchain.wallets)

@app.route('/create_wallet', methods=['GET', 'POST'])
def create_wallet():
    """Handle wallet creation and redirect to show the private key."""
    if request.method == 'POST':  # Handle form submission
        name = request.form['name']  # Get the wallet name from the form
        if name:  # Check if a name was provided
            wallet = blockchain.create_wallet(name)  # Create a new wallet
            # Redirect to show_private_key with public and private keys as URL parameters
            return redirect(url_for('show_private_key', public_key=wallet.get_public_key(), 
                                    private_key=wallet.get_private_key()))
        flash("Please enter a name.")  # Show error if no name is provided
    # Render the create_wallet.html template for GET requests
    return render_template('create_wallet.html')

@app.route('/show_private_key/<public_key>/<private_key>')
def show_private_key(public_key, private_key):
    """Display the wallet details and private key after creation."""
    if public_key in blockchain.wallets:  # Verify the wallet exists
        wallet = blockchain.wallets[public_key]  # Retrieve the wallet object
        # Render the show_private_key.html template with wallet and private key
        return render_template('show_private_key.html', wallet=wallet, private_key=private_key)
    flash("Wallet not found.")  # Show error if wallet doesn’t exist
    return redirect(url_for('index'))  # Redirect to home page

@app.route('/check_balance', methods=['GET', 'POST'])
def check_balance():
    """Check and display the balance of a wallet by public key."""
    if request.method == 'POST':  # Handle form submission
        public_key = request.form['public_key']  # Get the public key from the form
        balance = blockchain.check_balance(public_key)  # Query the balance
        if isinstance(balance, str):  # If balance is an error message (string)
            flash(balance)  # Display the error
        else:  # If balance is a number
            flash(f"Balance for {public_key[:10]}...: {balance}")  # Show truncated key and balance
        return redirect(url_for('index'))  # Redirect to home page
    # Render the check_balance.html template for GET requests
    return render_template('check_balance.html')

@app.route('/send_transaction', methods=['GET', 'POST'])
def send_transaction():
    """Handle sending a transaction with manual private key input."""
    if request.method == 'POST':  # Handle form submission
        sender_pub = request.form['sender_pub']  # Sender’s public key from dropdown
        private_key = request.form['private_key']  # Sender’s private key from input
        receiver_pub = request.form['receiver_pub']  # Receiver’s public key from dropdown
        amount = float(request.form['amount'])  # Transaction amount
        # Add the transaction to the blockchain, passing the private key for signing
        result = blockchain.add_transaction(sender_pub, receiver_pub, amount, private_key)
        flash(result)  # Display the result (success or error)
        return redirect(url_for('index'))  # Redirect to home page
    # Render the send_transaction.html template with wallet list for GET requests
    return render_template('send_transaction.html', wallets=blockchain.wallets)

@app.route('/mine_block', methods=['GET', 'POST'])
def mine_block():
    """Mine a new block and reward the miner."""
    if request.method == 'POST':  # Handle form submission
        miner_pub = request.form['miner_pub']  # Miner’s public key from dropdown
        if miner_pub in blockchain.wallets:  # Verify the miner exists
            blockchain.mine_block(miner_pub)  # Mine a block with the miner’s public key
            flash(f"Block mined by {blockchain.wallets[miner_pub].name}!")  # Success message
        else:
            flash("Invalid miner public key.")  # Error message
        return redirect(url_for('index'))  # Redirect to home page
    # Render the mine_block.html template with wallet list for GET requests
    return render_template('mine_block.html', wallets=blockchain.wallets)

@app.route('/save_blockchain', methods=['POST'])
def save_blockchain():
    """Save the current blockchain state to a file."""
    filename = blockchain.save_blockchain_to_file()  # Save blockchain and get filename
    flash(f"Blockchain saved to {filename}")  # Display the saved file path
    return redirect(url_for('index'))  # Redirect to home page

@app.route('/load_blockchain', methods=['GET', 'POST'])
def load_blockchain():
    """Load a blockchain state from a file."""
    if request.method == 'POST':  # Handle form submission
        filename = request.form['filename']  # Get the filename from the form
        result = blockchain.load_blockchain_from_file(filename)  # Load the blockchain
        flash(result)  # Display the result (success or error)
        return redirect(url_for('index'))  # Redirect to home page
    # Render the load_blockchain.html template for GET requests
    return render_template('load_blockchain.html')

if __name__ == '__main__':
    """Entry point for running the application."""
    blockchain.genesis_block()  # Create the genesis block when the app starts
    app.run(debug=True)  # Run the Flask app in debug mode on localhost:5000