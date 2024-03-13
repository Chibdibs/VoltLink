import hashlib
import time
from flask import Flask, jsonify, request


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0, hash=None):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = hash

    def compute_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 2  # difficulty of the proof of work algorithm

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)
        return self.last_block.index + 1  # Assuming the next block will contain the transaction

    @staticmethod
    def proof_of_work(self, block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        :param self:
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
    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        :param self:
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
        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash,
                          nonce=0)
        proof = self.proof_of_work(new_block)
        new_block.hash = proof # Explicitly set the block's hash attribute
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block.index

    @property
    def last_block(self):
        return self.chain[-1]


# Initialize Flask app
app = Flask(__name__)

blockchain = Blockchain()


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = [block.__dict__ for block in blockchain.chain]
    # for block in blockchain.chain:
    #     chain_data.append(block.__dict__)
    return jsonify(chain_data), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required_fields = ["sender", "recipient", "amount"]

    if not all(k in values for k in required_fields):
        return 'Missing values', 400

    index = blockchain.add_new_transaction(values)
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response)

# Add Flask routes for API endpoints


if __name__ == "__main__":
    app.run(debug=True)
