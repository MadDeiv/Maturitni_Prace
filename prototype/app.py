from flask import Flask, render_template, request, redirect, url_for, flash
from blockchain import Blockchain  # Import the Blockchain class for cryptocurrency logic

# Initialize the Flask application
app = Flask(__name__)  # Create a Flask instance with the current module name
app.secret_key = "crypto_prototype_secret"  # Set a secret key for session security (required for flash messages)

# Create a global Blockchain instance to manage the cryptocurrency state
blockchain = Blockchain()  # Instantiate the Blockchain class; holds wallets, blocks, and transactions

@app.route('/')
def index():
    """Render the home page with blockchain and wallet details."""
    # Pass the blockchain string and wallet dictionary to the index.html template for display
    return render_template('index.html', blockchain=blockchain.display_blockchain(), 
                           wallets=blockchain.wallets)

@app.route('/create_wallet', methods=['GET', 'POST'])
def create_wallet():
    """Handle wallet creation and redirect to show the private key."""
    if request.method == 'POST':  # Check if the request is a form submission
        name = request.form['name'].strip()  # Get the wallet name from the form and remove whitespace
        if name:  # Ensure a name was provided
            wallet = blockchain.create_wallet(name)  # Create a new wallet with the given name
            flash(f"Wallet '{name}' created successfully!", "success")  # Show a success message (green)
            # Redirect to show_private_key, passing public and private keys as URL parameters
            return redirect(url_for('show_private_key', public_key=wallet.get_public_key(), 
                                    private_key=wallet.get_private_key()))
        flash("Please enter a name.", "error")  # Show an error message (red) if no name is provided
    return render_template('create_wallet.html')  # Render the form for GET requests

@app.route('/show_private_key/<public_key>/<private_key>')
def show_private_key(public_key, private_key):
    """Display the wallet details and private key after creation."""
    if public_key in blockchain.wallets:  # Verify the wallet exists in the blockchain
        wallet = blockchain.wallets[public_key]  # Retrieve the wallet object using the public key
        # Render the template with wallet details and private key
        return render_template('show_private_key.html', wallet=wallet, private_key=private_key)
    flash("Wallet not found.", "error")  # Show an error (red) if the wallet isn’t found
    return redirect(url_for('index'))  # Redirect to the home page

@app.route('/check_balance', methods=['GET', 'POST'])
def check_balance():
    """Check and display the balance of a wallet by public key."""
    if request.method == 'POST':  # Handle form submission
        public_key = request.form['public_key'].strip()  # Get the public key from the form and clean it
        balance = blockchain.check_balance(public_key)  # Query the balance for this public key
        print(f"Checking balance for: {public_key}")  # Debug: log the key being checked
        if isinstance(balance, str):  # If the result is a string (error message)
            flash(balance, "error")  # Show the error message in red
        else:  # If the result is a number (balance)
            flash(f"Balance for {public_key[:10]}...: {balance}", "success")  # Show balance in green
        return redirect(url_for('index'))  # Redirect to the home page to display the message
    return render_template('check_balance.html')  # Render the form for GET requests

@app.route('/send_transaction', methods=['GET', 'POST'])
def send_transaction():
    """Handle sending a transaction with manual private key input."""
    if request.method == 'POST':  # Handle form submission
        sender_pub = request.form['sender_pub'].strip()  # Get sender’s public key from dropdown
        private_key = request.form['private_key'].strip()  # Get sender’s private key from input
        receiver_pub = request.form['receiver_pub'].strip()  # Get receiver’s public key from dropdown
        try:
            amount = float(request.form['amount'])  # Convert amount to float
            # Attempt to add the transaction to the blockchain
            result = blockchain.add_transaction(sender_pub, receiver_pub, amount, private_key)
            # Show result as success (green) if "added" is in the message, else error (red)
            flash(result, "success" if "added" in result.lower() else "error")
        except ValueError:  # Handle invalid amount input
            flash("Invalid amount entered.", "error")
        return redirect(url_for('index'))  # Redirect to home page to show the message
    # Render the transaction form with wallet list for GET requests
    return render_template('send_transaction.html', wallets=blockchain.wallets)

@app.route('/mine_block', methods=['GET', 'POST'])
def mine_block():
    """Mine a new block and reward the miner."""
    if request.method == 'POST':  # Handle form submission
        miner_pub = request.form['miner_pub'].strip()  # Get miner’s public key from dropdown
        if miner_pub in blockchain.wallets:  # Verify the miner exists
            blockchain.mine_block(miner_pub)  # Mine a new block and reward the miner
            flash(f"Block mined by {blockchain.wallets[miner_pub].name}!", "success")  # Show success (green)
        else:
            flash("Invalid miner public key.", "error")  # Show error (red) if miner not found
        return redirect(url_for('index'))  # Redirect to home page
    return render_template('mine_block.html', wallets=blockchain.wallets)  # Render form for GET

@app.route('/save_blockchain', methods=['POST'])
def save_blockchain():
    """Save the current blockchain state to a file."""
    filename = blockchain.save_blockchain_to_file()  # Save the blockchain and get the filename
    flash(f"Blockchain saved to {filename}", "success")  # Show success message (green)
    return redirect(url_for('index'))  # Redirect to home page

@app.route('/load_blockchain', methods=['GET', 'POST'])
def load_blockchain():
    """Load a blockchain state from a file."""
    if request.method == 'POST':  # Handle form submission
        filename = request.form['filename'].strip()  # Get the filename from the form
        result = blockchain.load_blockchain_from_file(filename)  # Attempt to load the blockchain
        # Show result as success (green) if "successfully" is in the message, else error (red)
        flash(result, "success" if "successfully" in result.lower() else "error")
        return redirect(url_for('index'))  # Redirect to home page
    return render_template('load_blockchain.html')  # Render form for GET requests

if __name__ == '__main__':
    """Entry point for running the application."""
    print("Starting the app...")
    blockchain.genesis_block()  # Create the genesis block when the app starts
    app.run(debug=True)  # Run the Flask app in debug mode on localhost:5000