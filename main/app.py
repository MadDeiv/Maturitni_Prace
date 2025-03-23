from flask import Flask, render_template, request, redirect, url_for, flash
from blockchain import Blockchain

app = Flask(__name__)
app.secret_key = "crypto_prototype_secret"
blockchain = Blockchain()

@app.route('/')
def index():
    return render_template('index.html', blockchain=blockchain.display_blockchain(), 
                           wallets=blockchain.wallets)

@app.route('/create_wallet', methods=['GET', 'POST'])
def create_wallet():
    if request.method == 'POST':
        name = request.form['name']
        if name:
            wallet = blockchain.create_wallet(name)  # Create wallet once
            # Pass public_key and private_key to show_private_key
            return redirect(url_for('show_private_key', public_key=wallet.get_public_key(), 
                                    private_key=wallet.get_private_key()))
        flash("Please enter a name.")
    return render_template('create_wallet.html')

@app.route('/show_private_key/<public_key>/<private_key>')
def show_private_key(public_key, private_key):
    if public_key in blockchain.wallets:
        wallet = blockchain.wallets[public_key]  # Use existing wallet
        return render_template('show_private_key.html', wallet=wallet, private_key=private_key)
    flash("Wallet not found.")
    return redirect(url_for('index'))

@app.route('/check_balance', methods=['GET', 'POST'])
def check_balance():
    if request.method == 'POST':
        public_key = request.form['public_key']
        balance = blockchain.check_balance(public_key)
        if isinstance(balance, str):
            flash(balance)
        else:
            flash(f"Balance for {public_key[:10]}...: {balance}")
        return redirect(url_for('index'))
    return render_template('check_balance.html')

@app.route('/send_transaction', methods=['GET', 'POST'])
def send_transaction():
    if request.method == 'POST':
        sender_pub = request.form['sender_pub']
        private_key = request.form['private_key']
        receiver_pub = request.form['receiver_pub']
        amount = float(request.form['amount'])
        result = blockchain.add_transaction(sender_pub, receiver_pub, amount, private_key)
        flash(result)
        return redirect(url_for('index'))
    return render_template('send_transaction.html', wallets=blockchain.wallets)

@app.route('/mine_block', methods=['GET', 'POST'])
def mine_block():
    if request.method == 'POST':
        miner_pub = request.form['miner_pub']
        if miner_pub in blockchain.wallets:
            blockchain.mine_block(miner_pub)
            flash(f"Block mined by {blockchain.wallets[miner_pub].name}!")
        else:
            flash("Invalid miner public key.")
        return redirect(url_for('index'))
    return render_template('mine_block.html', wallets=blockchain.wallets)

@app.route('/save_blockchain', methods=['POST'])
def save_blockchain():
    filename = blockchain.save_blockchain_to_file()
    flash(f"Blockchain saved to {filename}")
    return redirect(url_for('index'))

@app.route('/load_blockchain', methods=['GET', 'POST'])
def load_blockchain():
    if request.method == 'POST':
        filename = request.form['filename']
        result = blockchain.load_blockchain_from_file(filename)
        flash(result)
        return redirect(url_for('index'))
    return render_template('load_blockchain.html')

if __name__ == '__main__':
    blockchain.genesis_block()
    app.run(debug=True)