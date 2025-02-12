#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# Add parent directory to Python path to find hivemind package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import logging
import os
from typing import Optional, List, Dict, Any, Union

from hivemind.state import HivemindOption, HivemindOpinion, HivemindState
from hivemind.issue import HivemindIssue
from hivemind.option import HivemindOption

# Set up logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/debug.log'),
        logging.StreamHandler()  # This will also print to console
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Hivemind Insights")
import sys
import os

# Add parent directory to Python path to find hivemind package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Optional, List, Dict, Any, Union

from hivemind.state import HivemindOption, HivemindOpinion, HivemindState
from hivemind.issue import HivemindIssue

# Initialize FastAPI app
app = FastAPI(title="Hivemind Insights")

# Set up logging
logging.basicConfig(level=logging.DEBUG)
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/debug.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
logger = logging.getLogger('hivemind')
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
logger.info('Hivemind Insights FastAPI startup')

# Mount static files and templates
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

class IPFSHashRequest(BaseModel):
    ipfs_hash: str

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/fetch_state")
async def fetch_state(request: IPFSHashRequest):
    try:
        ipfs_hash = request.ipfs_hash
        if not ipfs_hash:
            raise HTTPException(status_code=400, detail="IPFS hash is required")
            
        logger.info(f"Attempting to load state from IPFS with CID: {ipfs_hash}")
        
        from ipfs_dict_chain.IPFS import connect, get_json, IPFSError
        import asyncio
        try:
            # Run the blocking IPFS operations in a thread pool
            loop = asyncio.get_event_loop()
            try:
                await loop.run_in_executor(None, lambda: connect('127.0.0.1', 5001))
                logger.info("Successfully connected to IPFS daemon")
                
                # Get the raw state data
                raw_data = await loop.run_in_executor(None, lambda: get_json(cid=ipfs_hash))
                logger.info(f"Successfully read raw data from IPFS")
                logger.info(f"Raw data: {raw_data}")
                
                if not isinstance(raw_data, dict):
                    raise HTTPException(status_code=400, detail="Invalid data format")
                
                # Create HivemindState object
                state = HivemindState()
                state.__dict__.update(raw_data)
                
                # First get the issue data from IPFS
                issue_cid = raw_data.get('hivemind_id')
                if issue_cid:
                    try:
                        issue_data = await loop.run_in_executor(None, lambda: get_json(cid=issue_cid))
                        logger.info(f"Successfully fetched issue data: {issue_data}")
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
                        logger.error(f"Failed to fetch issue data: {str(e)}")
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
                        option_data = await loop.run_in_executor(None, lambda: get_json(cid=option_cid))
                        option = {
                            'cid': option_cid,
                            'value': option_data.get('value', 'N/A'),
                            'text': option_data.get('text', 'Unnamed Option')
                        }
                        options.append(option)
                    except Exception as e:
                        logger.error(f"Failed to fetch option data for {option_cid}: {str(e)}")
                        options.append({
                            'cid': option_cid,
                            'value': 'Failed to load',
                            'text': 'Failed to load option data'
                        })

                opinions = raw_data.get('opinions', [])
                total_opinions = len(opinions[0]) if opinions and len(opinions) > 0 else 0

                # Load full opinion data using HivemindOpinion
                full_opinions = []
                for question_opinions in opinions:
                    question_data = {}
                    for address, opinion_info in question_opinions.items():
                        try:
                            opinion = HivemindOpinion()
                            # Run the opinion loading in the same event loop
                            opinion_data = await loop.run_in_executor(None, lambda: get_json(cid=opinion_info['opinion_cid']))
                            opinion.__dict__.update(opinion_data)
                            logger.info(f"Loaded opinion data for {address}: {opinion.__dict__}")
                            
                            # Extract ranking based on the data format
                            ranking = None
                            if hasattr(opinion, 'ranking'):
                                if isinstance(opinion.ranking, list):
                                    # Legacy format where ranking is directly a list
                                    ranking = opinion.ranking
                                elif isinstance(opinion.ranking, dict):
                                    # Dict format with fixed/auto_high/auto_low
                                    if 'fixed' in opinion.ranking:
                                        ranking = opinion.ranking['fixed']
                                elif hasattr(opinion.ranking, 'fixed') and opinion.ranking.fixed:
                                    # Ranking object with fixed ranking
                                    ranking = opinion.ranking.fixed
                                    
                            logger.info(f"Extracted ranking for {address}: {ranking}")
                            question_data[address] = {
                                'opinion_cid': opinion_info['opinion_cid'],
                                'timestamp': opinion_info['timestamp'],
                                'ranking': ranking
                            }
                        except Exception as e:
                            logger.error(f"Failed to load opinion data for {address}: {str(e)}")
                            question_data[address] = {
                                'opinion_cid': opinion_info['opinion_cid'],
                                'timestamp': opinion_info['timestamp'],
                                'ranking': None
                            }
                    full_opinions.append(question_data)

                logger.info(f"Extracted issue info: {issue_info}")

                return {
                    'issue': issue_info,
                    'options': options,
                    'total_opinions': total_opinions,
                    'opinions': full_opinions,
                    'hivemind_id': raw_data.get('hivemind_id'),
                    'previous_cid': raw_data.get('previous_cid')
                }
                
            except Exception as e:
                logger.error(f"Failed to read data from IPFS: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to read data from IPFS: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Error connecting to IPFS: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to IPFS: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing request")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/test_ipfs")
async def test_ipfs():
    """Test endpoint to verify IPFS connectivity."""
    try:
        from ipfs_dict_chain.IPFS import connect, get_json, IPFSError
        
        # Try to connect to IPFS
        try:
            connect('127.0.0.1', 5001)
            logger.info("Successfully connected to IPFS daemon")
            return {"status": "success", "message": "Successfully connected to IPFS daemon"}
            
        except Exception as e:
            logger.error(f"Failed to connect to IPFS daemon: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to IPFS daemon: {str(e)}"
            )
            
    except Exception as e:
        logger.exception("Error testing IPFS connection")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
