import unittest
import requests
import json
from subprocess import Popen
import time


class BlockchainTransactionTests(unittest.TestCase):
    def setUp(self):
        # Start the Flask application in a separate process for testing
        # Ensure your app.py (or however your main app script is named) is correctly referenced here
        self.flask_app = Popen(["python", "app.py"])
        time.sleep(1)  # Give the server a second to ensure it starts

    def tearDown(self):
        self.flask_app.terminate()

    def test_transaction_creation(self):
        """Test creating a new transaction via the API"""
        transaction_data = {
            'sender': 'Alice',
            'recipient': 'Bob',
            'amount': 5,
        }
        response = requests.post('http://127.0.0.1:5000/transactions/new', json=transaction_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Transaction will be added to Block', response.json()['message'])

    # More tests here


if __name__ == '__main__':
    unittest.main()
