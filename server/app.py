#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import queue
import atexit
import asyncio

# Add parent directory to Python path to find hivemind package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import logging
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
import os
from typing import Optional, List, Dict, Any, Union

from hivemind.state import HivemindOption, HivemindOpinion, HivemindState
from hivemind.issue import HivemindIssue
from hivemind.option import HivemindOption

# Set up logging with queue handler
def setup_logging():
    # Create log directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Create queue for logging
    log_queue = queue.Queue(-1)  # No limit on size

    # Configure queue handler
    queue_handler = QueueHandler(log_queue)
    
    # Configure root logger with queue handler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(queue_handler)
    
    # Configure file handler for the queue listener
    file_handler = RotatingFileHandler(
        'logs/debug.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        delay=True  # Delay file creation until first log
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    
    # Create and start queue listener
    console_handler = logging.StreamHandler()  # For console output
    console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    
    listener = QueueListener(
        log_queue,
        file_handler,
        console_handler,
        respect_handler_level=True
    )
    listener.start()
    
    # Register cleanup on exit
    atexit.register(listener.stop)
    
    return listener

# Initialize logging
log_listener = setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Hivemind Insights")

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

        # Load the state in a thread
        state = await asyncio.to_thread(lambda: HivemindState(cid=ipfs_hash))
        
        # Get basic info that doesn't require IPFS calls
        basic_info = {
            'hivemind_id': state.hivemind_id,
            'num_options': len(state.options),
            'num_opinions': len(state.opinions[0]) if state.opinions else 0,
            'is_final': state.final
        }
        
        # Load issue details asynchronously
        if state.hivemind_id:
            issue = await asyncio.to_thread(lambda: HivemindIssue(cid=state.hivemind_id))
            basic_info['issue'] = {
                'name': issue.name or 'Unnamed Issue',
                'description': issue.description or 'No description available',
                'tags': issue.tags or [],
                'questions': issue.questions or [],
                'answer_type': issue.answer_type or 'Unknown',
                'constraints': issue.constraints,
                'restrictions': issue.restrictions
            }
            logger.info(f"Loaded issue details for {state.hivemind_id}")
        
        # Load options asynchronously
        options = []
        for option_hash in state.options:
            try:
                option = await asyncio.to_thread(lambda h=option_hash: HivemindOption(cid=h))
                options.append({
                    'cid': option_hash,
                    'value': option.value if hasattr(option, 'value') else None,
                    'text': option.text if hasattr(option, 'text') else None
                })
                logger.info(f"Loaded option {option_hash}")
            except Exception as e:
                logger.error(f"Failed to load option {option_hash}: {str(e)}")
                options.append({
                    'cid': option_hash,
                    'value': None,
                    'text': f"Failed to load: {str(e)}"
                })
        
        # Add options to response
        basic_info['options'] = options
        
        # Load opinions asynchronously
        full_opinions = []
        for question_index, question_opinions in enumerate(state.opinions):
            question_data = {}
            for address, opinion_info in question_opinions.items():
                try:
                    # Load opinion data in a thread
                    opinion = await asyncio.to_thread(lambda cid=opinion_info['opinion_cid']: HivemindOpinion(cid=cid))
                    
                    # Extract ranking based on the data format
                    ranking = None
                    if hasattr(opinion, 'ranking'):
                        if isinstance(opinion.ranking, list):
                            ranking = opinion.ranking
                        elif isinstance(opinion.ranking, dict):
                            ranking = opinion.ranking.get('fixed')
                        elif hasattr(opinion.ranking, 'fixed'):
                            ranking = opinion.ranking.fixed
                    
                    logger.info(f"Loaded opinion for {address} in question {question_index}")
                    question_data[address] = {
                        'opinion_cid': opinion_info['opinion_cid'],
                        'timestamp': opinion_info['timestamp'],
                        'ranking': ranking
                    }
                except Exception as e:
                    logger.error(f"Failed to load opinion for {address} in question {question_index}: {str(e)}")
                    question_data[address] = {
                        'opinion_cid': opinion_info['opinion_cid'],
                        'timestamp': opinion_info['timestamp'],
                        'ranking': None,
                        'error': str(e)
                    }
            full_opinions.append(question_data)
        
        # Add opinions to response
        basic_info['opinions'] = full_opinions
        basic_info['total_opinions'] = len(state.opinions[0]) if state.opinions else 0
        basic_info['previous_cid'] = state.previous_cid
        
        logger.info(f"Completed loading state info with {len(options)} options and {basic_info['total_opinions']} opinions")
        return basic_info

    except Exception as e:
        logger.exception(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
