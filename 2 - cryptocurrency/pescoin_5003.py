import datetime
import hashlib
import json
import requests
from flask import Flask, jsonify, request
from uuid import uuid4
from urllib.parse import urlparse

def create_node_address():
    return str(uuid4()).replace('-','')

class Blockchain: #BUILDING A BLOCKCHAIN
    
    def __init__(self):
        self.chain = []
        self.transactions = [] 
        self.create_block(proof=1, previous_hash ='0')
        self.nodes = set()
    
    def create_block(self, proof, previous_hash):
        block = {'index':len(self.chain)+1,
                 'timestamp':str(datetime.datetime.now()),
                 'proof':proof,
                 'previous_hash':previous_hash,
                 'transactions': self.transactions}
        self.transactions = []   
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]=='0000':
                check_proof = True
            else:
                new_proof+=1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]!='0000':
                return False
            previous_block = block
            block_index+=1
            return True
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender':sender,
                                  'receiver':receiver,
                                  'amount':amount})
        previous_block=self.get_previous_block()
        return previous_block['index']+1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
    
app = Flask(__name__) #CREATING A WEB APP
node_address = create_node_address() #CREATING AN ADDRESS FOR THE NODE ON PORT 500 
blockchain = Blockchain() #CREATING A BLOCKCHAIN

@app.route('/mine_block', methods=['GET']) #MINING A NEW BLOCK
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'You', amount = 1 )
    block = blockchain.create_block(proof, previous_hash)
    response = {'message':'Congratulations, you just mined a block',
                'index':block['index'],
                'timestamp':block['timestamp'],
                'proof':block['proof'],
                'previous_hash':block['previous_hash'],
                'transactions':block['transactions']}
    return jsonify(response), 200

@app.route('/get_chain', methods=['GET']) #GET A BLOCKCHAIN
def get_chain():
    response =  {'chain':blockchain.chain,
                'length':len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/is_valid', methods=['GET']) #CHECK IF THE BLOCKCHAIN IS VALID OR NOT
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message':'yes'}
    else:
        response = {'message':'no'}
    return jsonify(response), 200

@app.route('/add_transaction', methods=['POST']) #ADDING A NEW TRANSATION TO THE BLOCKCHAIN
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender','receiver','amount']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of transaction are missing', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'messagge': f'This transaction will be added to block {index}'}
    return jsonify(response), 201

@app.route('/connect_node', methods=['POST']) #DECENTRALIZING THE BLOCKCHAIN
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No nodes', 400
    for node in nodes:
        blockchain.add_node(node)
        response = {'message': 'All nodes are now connected',
                    'total_nodes': list(blockchain.nodes)}
        return jsonify(response),201
     
@app.route('/replace_chain', methods=['GET']) #REPLACING THE CHAIN BY THE LONGEST IF NEEDED
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message':'done',
                    'new_chain': blockchain.chain}
    else:
        response = {'message':'the chain is already the largest one',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200

app.run(host='0.0.0.0',port=5003) #RUNNING THE APP



