from flask import Flask, render_template, request, jsonify
from hivemind.state import HivemindOption, HivemindOpinion, HivemindState
from hivemind.issue import HivemindIssue
import logging
from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Set up logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/debug.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Hivemind Insights startup')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch_state', methods=['POST'])
def fetch_state():
    try:
        ipfs_hash = request.json.get('ipfs_hash')
        if not ipfs_hash:
            return jsonify({'error': 'IPFS hash is required'}), 400
            
        app.logger.info(f"Attempting to load state from IPFS with CID: {ipfs_hash}")
        
        from ipfs_dict_chain.IPFS import connect, get_json, IPFSError
        try:
            connect('127.0.0.1', 5001)
            app.logger.info("Successfully connected to IPFS daemon")
            
            try:
                # Get the raw state data
                raw_data = get_json(cid=ipfs_hash)
                app.logger.info(f"Successfully read raw data from IPFS")
                app.logger.info(f"Raw data: {raw_data}")
                
                if not isinstance(raw_data, dict):
                    return jsonify({'error': 'Invalid data format'}), 400
                
                # Create HivemindState object
                state = HivemindState()
                state.__dict__.update(raw_data)
                
                # First get the issue data from IPFS
                issue_cid = raw_data.get('hivemind_id')
                if issue_cid:
                    try:
                        issue_data = get_json(cid=issue_cid)
                        app.logger.info(f"Successfully fetched issue data: {issue_data}")
                        issue = HivemindIssue()
                        issue.__dict__.update(issue_data)
                        
                        issue_info = {
                            'name': issue.name or 'Unnamed Issue',
                            'description': issue.description or 'No description available',
                            'tags': issue.tags or [],
                            'questions': issue.questions or [],
                            'answer_type': issue.answer_type or 'Unknown',
                            'constraints': issue.constraints,
                            'restrictions': issue.restrictions,
                            'hivemind_id': issue_cid
                        }
                    except Exception as e:
                        app.logger.error(f"Failed to fetch issue data: {str(e)}")
                        issue_info = {
                            'name': 'Unnamed Issue',
                            'description': 'Failed to load issue data',
                            'tags': [],
                            'questions': [],
                            'answer_type': 'Unknown',
                            'constraints': None,
                            'restrictions': None,
                            'hivemind_id': issue_cid
                        }
                else:
                    issue_info = {
                        'name': 'Unnamed Issue',
                        'description': 'No issue ID available',
                        'tags': [],
                        'questions': [],
                        'answer_type': 'Unknown',
                        'constraints': None,
                        'restrictions': None,
                        'hivemind_id': None
                    }

                # Extract options and opinions
                options = []
                for option_cid in raw_data.get('options', []):
                    try:
                        option_data = get_json(cid=option_cid)
                        option = {
                            'cid': option_cid,
                            'value': option_data.get('value', 'N/A'),
                            'text': option_data.get('text', 'Unnamed Option')
                        }
                        options.append(option)
                    except Exception as e:
                        app.logger.error(f"Failed to fetch option data for {option_cid}: {str(e)}")
                        options.append({
                            'cid': option_cid,
                            'value': 'Failed to load',
                            'text': 'Failed to load option data'
                        })

                opinions = raw_data.get('opinions', [])
                total_opinions = len(opinions[0]) if opinions and len(opinions) > 0 else 0

                app.logger.info(f"Extracted issue info: {issue_info}")

                return jsonify({
                    'issue': issue_info,
                    'options': options,
                    'total_opinions': total_opinions,
                    'hivemind_id': raw_data.get('hivemind_id')
                })
                
            except Exception as e:
                app.logger.error(f"Failed to read data from IPFS: {str(e)}")
                return jsonify({
                    'error': 'Failed to read data from IPFS',
                    'details': str(e)
                }), 500
                
        except Exception as e:
            app.logger.error(f"Error connecting to IPFS: {str(e)}")
            return jsonify({
                'error': 'Failed to connect to IPFS',
                'details': str(e)
            }), 500
            
    except Exception as e:
        app.logger.exception("Error processing request")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

def serialize_option(option):
    """Serialize a HivemindOption object to make it JSON-safe.
    
    Args:
        option: HivemindOption object
        
    Returns:
        Dictionary with all values converted to JSON-safe types
    """
    try:
        return {
            'cid': str(option.cid),
            'text': str(option.text) if hasattr(option, 'text') else None,
            'value': str(option.value) if hasattr(option, 'value') else None,
            'answer_type': str(option._answer_type) if hasattr(option, '_answer_type') else None,
            'hivemind_id': str(option.hivemind_id) if hasattr(option, 'hivemind_id') else None
        }
    except Exception as e:
        app.logger.error(f"Error serializing option: {str(e)}")
        return {
            'cid': str(option.cid),
            'error': str(e)
        }

def get_total_opinions(state):
    """Calculate the total number of opinions from the state.
    
    Args:
        state: HivemindState object
        
    Returns:
        int: Total number of opinions across all questions
    """
    total = 0
    for opinion_dict in state.opinions:
        if isinstance(opinion_dict, dict):
            total += len(opinion_dict)
    return total

@app.route('/api/test_ipfs', methods=['GET'])
def test_ipfs():
    """Test endpoint to verify IPFS connectivity."""
    try:
        from ipfs_dict_chain.IPFS import connect, get_json, IPFSError
        
        # Try to connect to IPFS
        try:
            connect('127.0.0.1', 5001)
            app.logger.info("Successfully connected to IPFS daemon")
        except Exception as e:
            app.logger.error(f"Failed to connect to IPFS daemon: {str(e)}")
            return jsonify({
                'error': 'Failed to connect to IPFS daemon',
                'details': str(e)
            }), 500
        
        # Try to read a test hash (this is just a test hash, it might not exist)
        test_hash = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
        try:
            data = get_json(test_hash)
            return jsonify({
                'status': 'success',
                'message': 'Successfully connected to IPFS',
                'data': data
            })
        except IPFSError as e:
            app.logger.error(f"Failed to read test hash: {str(e)}")
            return jsonify({
                'error': 'Failed to read test hash',
                'details': str(e)
            }), 500
            
    except Exception as e:
        app.logger.exception("Error testing IPFS connection")
        return jsonify({
            'error': 'Error testing IPFS connection',
            'details': str(e)
        }), 500

@app.route('/api/test_opinion', methods=['POST'])
def test_opinion():
    """Test endpoint to verify opinion loading."""
    try:
        opinion_hash = request.json.get('opinion_hash')
        if not opinion_hash:
            return jsonify({'error': 'Opinion hash is required'}), 400
            
        # Try to connect to IPFS first
        from ipfs_dict_chain.IPFS import connect, IPFSError
        try:
            connect('127.0.0.1', 5001)
            app.logger.info("Successfully connected to IPFS daemon")
        except Exception as e:
            app.logger.error(f"Failed to connect to IPFS daemon: {str(e)}")
            return jsonify({
                'error': 'Failed to connect to IPFS daemon',
                'details': str(e)
            }), 500
            
        # Try to load the opinion
        try:
            opinion = HivemindOpinion(cid=opinion_hash)
            return jsonify({
                'status': 'success',
                'opinion': {
                    'cid': opinion_hash,
                    'question_index': opinion.question_index,
                    'ranking': opinion.ranking.get(),
                    'hivemind_id': opinion.hivemind_id
                }
            })
        except Exception as e:
            app.logger.error(f"Failed to load opinion: {str(e)}")
            return jsonify({
                'error': 'Failed to load opinion',
                'details': str(e)
            }), 500
            
    except Exception as e:
        app.logger.exception("Error testing opinion loading")
        return jsonify({
            'error': 'Error testing opinion loading',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
