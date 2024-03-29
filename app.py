import hashlib
import time
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request


class Block:
    def __init__(self, block_index, transactions, timestamp, previous_hash, nonce=0, block_hash=None):
        self.index = block_index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.block_hash = block_hash

    def compute_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 2  # difficulty of the proof of work algorithm

    def __init__(self):
        self.nodes = set()  # A set to store the network's nodes
        self.current_transactions = []
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.block_hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    def add_block(self, block):
        """
        A function that adds the block to the chain after verification.
        Verification includes checking that the previous hash referred in the block
        matches the hash of the latest block in the chain.
        :param block:
        :return:
        """
        if self.last_block.block_hash != block.previous_hash or not self.is_valid_proof(block, block.block_hash):
            return False
        self.chain.append(block)
        return True

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)
        return self.last_block.index + 1  # Assuming the next block will contain the transaction

    @staticmethod
    def proof_of_work(block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        :param block:
        :return:
        """
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    @staticmethod
    def is_valid_proof(block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        :param block:
        :param block_hash:
        :return:
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def mine(self):
        if not self.unconfirmed_transactions:
            return False  # No transactions to mine

        last_block = self.last_block
        new_block = Block(block_index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.block_hash,
                          nonce=0)
        proof = self.proof_of_work(new_block)
        new_block.block_hash = proof  # Explicitly set the block's hash attribute
        if self.add_block(new_block):  # Adjusted to pass only the new block
            self.unconfirmed_transactions = []  # Clear the list of unconfirmed transactions after unsuccessful mining
            return new_block.index
        else:
            return False

    def register_node(self, address):
        """
        Add a new node to the list of nodes.
        :param address:
        :return:
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            response = requests.get(f'https://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False

    @staticmethod
    def valid_chain(chain):
        """
        Determine if a given blockchain is valid.
        :param chain:
        :return:
        """
        # Check if genesis block is valid. This step might involve specific checks
        # depending on how genesis block is structured.

        # Starting from the second block, verify the hash and the linkage
        for i in range(1, len(chain)):
            current_block_data = chain[i]
            previous_block_data = chain[i-1]

            # Recreate Block instances from the stored data if necessary
            # This step depends on how your block data is structured
            current_block = Block(block_index=current_block_data['index'],
                                  transactions=current_block_data['transactions'],
                                  timestamp=current_block_data['timestamp'],
                                  previous_hash=current_block_data['previous_hash'],
                                  nonce=current_block_data['nonce'],
                                  block_hash=current_block_data.get('block_hash'))

            previous_block = Block(block_index=previous_block_data['index'],
                                   transactions=previous_block_data['transactions'],
                                   timestamp=previous_block_data['timestamp'],
                                   previous_hash=previous_block_data['previous_hash'],
                                   nonce=previous_block_data['nonce'],
                                   block_hash=previous_block_data.get('block_hash'))

            # Compute the hash of the previous block and ensure linkage
            if current_block.previous_hash != previous_block.compute_hash():
                return False

            # Validate the proof of work of the current block
            if (not current_block.block_hash.startswith('0' * Blockchain.difficulty)
                    or current_block.block_hash != current_block.compute_hash()):
                return False

        return True

    @property
    def last_block(self):
        return self.chain[-1]


# Initialize Flask app
app = Flask(__name__)
blockchain = Blockchain()


# Add Flask routes for API endpoints


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = [block.__dict__ for block in blockchain.chain]
    return jsonify(chain_data), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required_fields = ["sender", "recipient", "amount"]

    if not all(k in values for k in required_fields):
        return 'Missing values', 400

    block_index = blockchain.add_new_transaction(values)
    response = {'message': f'Transaction will be added to Block {block_index}'}
    return jsonify(response)


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/mine', methods=['GET'])
def mine():
    # Step 1: (Optional) Validate unconfirmed transactions
    # This step depends on your application's specific requirements

    # Step 2: Create a new block
    last_block = blockchain.last_block
    new_block = Block(block_index=last_block.index + 1,
                      transactions=blockchain.unconfirmed_transactions,
                      timestamp=time.time(),
                      previous_hash=last_block.block_hash)

    # Step 3: Find a proof-of-work
    proof = blockchain.proof_of_work(new_block)

    # Step 4: Add the new block to the chain
    new_block.block_hash = proof  # Set the block's hash to the proof found
    added = blockchain.add_block(new_block)

    # Step 5: Respond to the request
    if added:
        response = {
            'message': 'New block mined successfully',
            'block_number': new_block.index,
            'transactions': new_block.transactions,
            'nonce': new_block.nonce,
            'previous_hash': new_block.previous_hash,
            'hash': new_block.block_hash
        }
        # Clear unconfirmed transactions
        blockchain.unconfirmed_transactions = []
    else:
        response = {'message': 'New block failed to be mined'}

    return jsonify(response), 200


# Basic node integration
@app.route('/register_node', method=['POST'])
def register_node():
    values = request.get_json()
    node = values.get('node')
    if node is None:
        return "Error: Please supply a valid node", 400

    blockchain.register_node(node)
    return jsonify({'message': f'Node {node} registered successfully'}), 200


# Node endpoint
@app.route('/nodes', methods=['GET'])
def get_nodes():
    nodes = list(blockchain.nodes)
    return jsonify({'nodes': nodes}), 200


# Basic network synchronization
@app.route('/consensus', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {'message': 'Our chain was replaced', 'new_chain': blockchain.chain}
    else:
        response = {'message': 'Our chain is authoritative', 'chain': blockchain.chain}
    return jsonify(response), 200


@app.route('/')
def index():
    return '''
    <h1>Welcome to the VoltLink Blockchain</h1>
    <p>A simple blockchain implementation for peer-to-peer renewable energy trading.</p>
    <ul>
        <li><a href="/chain">View the current chain here</a></li>
        <li>Use a tool like Postman or cURL to interact with the API:</li>
        <ul>
            <li>Submit a new transaction with a POST request to <code>/transactions/new</code>.</li>
            <li>Mine a new block with a GET request to <code>/mine</code>.</li>
        </ul>
    </ul>
     '''


if __name__ == "__main__":
    app.run(debug=True)
