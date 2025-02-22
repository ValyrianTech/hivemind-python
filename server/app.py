#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import queue
import atexit
import asyncio
import time
from datetime import datetime
import csv

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

class StateLoadingStats:
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.start_time = time.time()
        self.state_cid = None
        self.state_load_time = 0
        self.options_load_time = 0
        self.opinions_load_time = 0
        self.calculation_time = 0
        self.total_time = 0
        self.num_questions = 0
        self.num_options = 0
        self.num_opinions = 0

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "state_cid": self.state_cid,
            "state_load_time": round(self.state_load_time, 3),
            "options_load_time": round(self.options_load_time, 3),
            "opinions_load_time": round(self.opinions_load_time, 3),
            "calculation_time": round(self.calculation_time, 3),
            "total_time": round(self.total_time, 3),
            "num_questions": self.num_questions,
            "num_options": self.num_options,
            "num_opinions": self.num_opinions
        }

def log_state_stats(stats: StateLoadingStats):
    """Log state loading statistics in a structured format."""
    stats_dict = stats.to_dict()
    logger.info("State Loading Statistics:")
    logger.info(f"  Timestamp: {stats_dict['timestamp']}")
    logger.info(f"  State CID: {stats_dict['state_cid']}")
    logger.info(f"  State Load Time: {stats_dict['state_load_time']}s")
    logger.info(f"  Options Load Time: {stats_dict['options_load_time']}s")
    logger.info(f"  Opinions Load Time: {stats_dict['opinions_load_time']}s")
    logger.info(f"  Calculation Time: {stats_dict['calculation_time']}s")
    logger.info(f"  Total Time: {stats_dict['total_time']}s")
    logger.info(f"  Number of Questions: {stats_dict['num_questions']}")
    logger.info(f"  Number of Options: {stats_dict['num_options']}")
    logger.info(f"  Number of Opinions: {stats_dict['num_opinions']}")

def log_stats_to_csv(stats: StateLoadingStats):
    """Write state loading statistics to CSV file."""
    stats_dict = stats.to_dict()
    csv_path = 'logs/state_loading_stats.csv'
    
    try:
        with open(csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                stats_dict['timestamp'],
                stats_dict['state_cid'],
                stats_dict['state_load_time'],
                stats_dict['options_load_time'],
                stats_dict['opinions_load_time'],
                stats_dict['calculation_time'],
                stats_dict['total_time'],
                stats_dict['num_questions'],
                stats_dict['num_options'],
                stats_dict['num_opinions']
            ])
    except Exception as e:
        logger.error(f"Failed to write stats to CSV: {str(e)}")

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
    
    # Create CSV file with headers if it doesn't exist
    csv_path = 'logs/state_loading_stats.csv'
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'state_cid',
                'state_load_time',
                'options_load_time',
                'opinions_load_time',
                'calculation_time',
                'total_time',
                'num_questions',
                'num_options',
                'num_opinions'
            ])
    
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

class HivemindIssueCreate(BaseModel):
    """Pydantic model for creating a new HivemindIssue."""
    name: str
    description: str
    questions: List[str]
    tags: List[str]
    answer_type: str
    constraints: Optional[Dict[str, Union[str, int, float, list]]] = None
    restrictions: Optional[Dict[str, Union[List[str], int]]] = None
    on_selection: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Render the landing page."""
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/insights", response_class=HTMLResponse)
async def insights_page(request: Request):
    """Render the insights page with IPFS data visualization."""
    return templates.TemplateResponse("insights.html", {"request": request})

@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    """Render the create page for new HivemindIssues."""
    return templates.TemplateResponse("create.html", {"request": request})

@app.post("/fetch_state")
async def fetch_state(request: IPFSHashRequest):
    stats = StateLoadingStats()
    
    try:
        ipfs_hash = request.ipfs_hash
        if not ipfs_hash:
            raise HTTPException(status_code=400, detail="IPFS hash is required")
        
        stats.state_cid = ipfs_hash
        logger.info(f"Attempting to load state from IPFS with CID: {ipfs_hash}")

        # Load the state in a thread
        state_start = time.time()
        state = await asyncio.to_thread(lambda: HivemindState(cid=ipfs_hash))
        stats.state_load_time = time.time() - state_start
        
        # Get basic info that doesn't require IPFS calls
        basic_info = {
            'hivemind_id': state.hivemind_id,
            'num_options': len(state.options),
            'num_opinions': len(state.opinions[0]) if state.opinions else 0,
            'is_final': state.final
        }
        
        stats.num_options = basic_info['num_options']
        stats.num_opinions = basic_info['num_opinions']
        
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
            stats.num_questions = len(issue.questions) if issue.questions else 0
            logger.info(f"Loaded issue details for {state.hivemind_id}")
        
        # Load options asynchronously
        options_start = time.time()
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
        stats.options_load_time = time.time() - options_start
        
        # Add options to response
        basic_info['options'] = options
        
        # Load opinions asynchronously
        opinions_start = time.time()
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
        stats.opinions_load_time = time.time() - opinions_start
        
        # Add opinions to response
        basic_info['opinions'] = full_opinions
        basic_info['total_opinions'] = len(state.opinions[0]) if state.opinions else 0
        basic_info['previous_cid'] = state.previous_cid
        
        # Calculate results for each question
        calculation_start = time.time()
        results = []
        for question_index in range(len(state.opinions)):
            try:
                logger.info(f"Calculating results for question {question_index}...")
                question_results = await asyncio.to_thread(lambda: state.calculate_results(question_index=question_index))
                sorted_options = await asyncio.to_thread(lambda: state.get_sorted_options(question_index=question_index))
                
                logger.info(f"Raw question results: {question_results}")
                logger.info(f"Sorted options: {[opt.cid() for opt in sorted_options]}")
                
                # Format results for the frontend
                formatted_results = []
                for option in sorted_options:
                    # Remove '/ipfs/' prefix if present when looking up the score
                    cid = option.cid()
                    if cid.startswith('/ipfs/'):
                        cid = cid[6:]  # Remove '/ipfs/' prefix
                    score = question_results.get(cid, {}).get('score', 0)
                    if score is None:
                        score = 0
                    logger.info(f"Option {option.cid()} - CID for lookup: {cid}, Score: {score}")
                    formatted_results.append({
                        'cid': option.cid(),
                        'value': option.value if hasattr(option, 'value') else None,
                        'text': option.text if hasattr(option, 'text') else str(option.value),
                        'score': round(score * 100, 2)  # Convert to percentage and round to 2 decimal places
                    })
                    
                # Calculate contribution scores
                contributions = await asyncio.to_thread(lambda: state.contributions(results=question_results, question_index=question_index))
                
                # Add contribution scores to opinions
                for address in full_opinions[question_index]:
                    contribution = contributions.get(address, 0)
                    full_opinions[question_index][address]['contribution_score'] = round(contribution * 100, 2)
                    
                results.append(formatted_results)
            except Exception as e:
                logger.error(f"Failed to calculate results for question {question_index}: {str(e)}")
                results.append([])
        stats.calculation_time = time.time() - calculation_start
        
        # Calculate total time
        stats.total_time = time.time() - stats.start_time
        
        # Log the final statistics
        log_state_stats(stats)
        log_stats_to_csv(stats)
        
        # Add statistics to response
        basic_info['stats'] = stats.to_dict()
        basic_info['results'] = results
        
        logger.info(f"Completed loading state info with {len(options)} options and {basic_info['total_opinions']} opinions")
        return basic_info

    except Exception as e:
        logger.error(f"Error processing state {ipfs_hash}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create_issue")
async def create_issue(issue: HivemindIssueCreate):
    """Create a new HivemindIssue and save it to IPFS."""
    try:
        # Create new HivemindIssue
        new_issue = HivemindIssue()
        new_issue.name = issue.name
        new_issue.description = issue.description
        new_issue.tags = issue.tags
        new_issue.answer_type = issue.answer_type
        new_issue.on_selection = issue.on_selection

        # Add questions
        for question in issue.questions:
            new_issue.add_question(question)

        # Set constraints if provided
        if issue.constraints:
            new_issue.set_constraints(issue.constraints)

        # Set restrictions if provided
        if issue.restrictions:
            new_issue.set_restrictions(issue.restrictions)

        # Save to IPFS and get CID
        cid = new_issue.save()
        return {"success": True, "cid": cid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
