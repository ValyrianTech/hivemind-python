#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import time
import asyncio
import logging

import queue
import atexit
from datetime import datetime
import csv
from pathlib import Path

# Add parent directory to Python path to find hivemind package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import logging
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
import os
from typing import Optional, List, Dict, Any, Union

from hivemind.state import HivemindOption, HivemindOpinion, HivemindState, verify_message
from hivemind.issue import HivemindIssue
from hivemind.option import HivemindOption
from hivemind.utils import generate_bitcoin_keypair, get_bitcoin_address
from hivemind.ranking import Ranking

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

# Create log directory if it doesn't exist
Path('logs').mkdir(exist_ok=True)

def setup_logging():
    """Setup logging configuration."""
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Create and configure file handler
    file_handler = RotatingFileHandler(
        'logs/debug.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    root_logger.addHandler(file_handler)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    root_logger.addHandler(console_handler)

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize state storage
STATES_DIR = Path(__file__).parent / "data"
STATES_DIR.mkdir(exist_ok=True, parents=True)

def load_state_mapping() -> Dict[str, Dict[str, Any]]:
    """Load all hivemind states from individual JSON files.
    
    Returns:
        Dict[str, Dict[str, Any]]: Mapping of hivemind IDs to their state data
    """
    try:
        mapping = {}
        for state_file in STATES_DIR.glob("*.json"):
            hivemind_id = state_file.stem
            try:
                with open(state_file, "r") as f:
                    mapping[hivemind_id] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state file {state_file}: {str(e)}")
        return mapping
    except Exception as e:
        logger.error(f"Failed to load state mapping: {str(e)}")
        return {}

def save_state_mapping(mapping: Dict[str, Dict[str, Any]]) -> None:
    """Save hivemind states to individual JSON files.
    
    Args:
        mapping: Dict mapping hivemind IDs to their state data
    """
    try:
        for hivemind_id, state_data in mapping.items():
            state_file = STATES_DIR / f"{hivemind_id}.json"
            try:
                with open(state_file, "w") as f:
                    json.dump(state_data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save state file {state_file}: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to save state mapping: {str(e)}")

class StateHashUpdate(BaseModel):
    """Pydantic model for updating state hash."""
    hivemind_id: str
    state_hash: str
    name: str
    description: str
    num_options: int
    num_opinions: int
    answer_type: str
    questions: List[str]
    tags: List[str]
    results: Optional[List[Dict[str, Any]]] = None

class OptionCreate(BaseModel):
    """Pydantic model for creating a new option."""
    hivemind_id: str
    value: Union[str, int, float]
    text: Optional[str] = None

class OpinionCreate(BaseModel):
    """Pydantic model for creating a new opinion."""
    hivemind_id: str
    question_index: int
    ranking: List[str]

class SignOpinionRequest(BaseModel):
    """Pydantic model for signing an opinion."""
    msg: str
    url: str

# Initialize FastAPI app
app = FastAPI(title="Hivemind Insights")

# Store active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}

# WebSocket endpoint for opinion notifications
@app.websocket("/ws/opinion/{opinion_hash}")
async def websocket_endpoint(websocket: WebSocket, opinion_hash: str):
    await websocket.accept()
    
    if opinion_hash not in active_connections:
        active_connections[opinion_hash] = []
    active_connections[opinion_hash].append(websocket)
    
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except:
        active_connections[opinion_hash].remove(websocket)
        if not active_connections[opinion_hash]:
            del active_connections[opinion_hash]

# Mount static files and templates
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

class IPFSHashRequest(BaseModel):
    cid: str

class HivemindIssueCreate(BaseModel):
    """Pydantic model for creating a new HivemindIssue."""
    name: str
    description: str
    questions: List[str]
    tags: List[str]
    answer_type: str
    constraints: Optional[Dict[str, Union[str, int, float, list, dict]]] = None
    restrictions: Optional[Dict[str, Union[List[str], int]]] = None
    on_selection: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Render the landing page."""
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/insights", response_class=HTMLResponse)
async def insights_page(request: Request):
    """Render the insights page with IPFS data visualization."""
    return templates.TemplateResponse("insights.html", {
        "request": request,
        "initial_cid": request.query_params.get("cid", "")
    })

@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    """Render the create page for new HivemindIssues."""
    return templates.TemplateResponse("create.html", {"request": request})

@app.get("/states", response_class=HTMLResponse)
async def states_page(request: Request):
    """Display overview of all hivemind states."""
    try:
        mapping = load_state_mapping()
        
        # Get file modification times and sort by most recent
        state_times = []
        for hivemind_id in mapping:
            state_file = STATES_DIR / f"{hivemind_id}.json"
            try:
                mtime = state_file.stat().st_mtime
                state_times.append((hivemind_id, mtime))
            except Exception as e:
                logger.error(f"Failed to get modification time for {state_file}: {str(e)}")
                state_times.append((hivemind_id, 0))  # Put files with errors at the end
        
        # Sort by modification time (most recent first)
        sorted_states = sorted(state_times, key=lambda x: x[1], reverse=True)
        
        # Add state info to each entry
        states = []
        for hivemind_id, _ in sorted_states:
            state_info = mapping[hivemind_id]
            states.append(dict(state_info, hivemind_id=hivemind_id))
        
        return templates.TemplateResponse("states.html", {
            "request": request,
            "states": states
        })
    except Exception as e:
        logger.error(f"Error loading states page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch_state")
async def fetch_state(request: IPFSHashRequest):
    stats = StateLoadingStats()
    
    try:
        cid = request.cid
        if not cid:
            raise HTTPException(status_code=400, detail="CID is required")
        
        stats.state_cid = cid
        logger.info(f"Attempting to load state from IPFS with CID: {cid}")

        # Load the state in a thread
        state_start = time.time()
        state = await asyncio.to_thread(lambda: HivemindState(cid=cid))
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
                'restrictions': issue.restrictions,
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
        full_results = []  # Keep full results for the frontend
        for question_index in range(len(state.opinions)):
            try:
                logger.info(f"Calculating results for question {question_index}...")
                question_results = await asyncio.to_thread(lambda: state.calculate_results(question_index=question_index))
                sorted_options = await asyncio.to_thread(lambda: state.get_sorted_options(question_index=question_index))
                
                logger.info(f"Raw question results: {question_results}")
                logger.info(f"Sorted options: {[opt.cid() for opt in sorted_options]}")
                
                # Format full results for the frontend
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
                        'text': option.text if hasattr(option, 'text') else str(option.value) if hasattr(option, 'value') else 'Unnamed Option',
                        'score': round(score * 100, 2)  # Convert to percentage and round to 2 decimal places
                    })
                
                # Calculate contribution scores
                contributions = await asyncio.to_thread(lambda: state.contributions(results=question_results, question_index=question_index))
                
                # Add contribution scores to opinions
                for address in full_opinions[question_index]:
                    contribution = contributions.get(address, 0)
                    full_opinions[question_index][address]['contribution_score'] = round(contribution * 100, 2)
                
                full_results.append(formatted_results)
                
                # Store just the winning option for the state mapping
                if sorted_options:
                    winning_option = sorted_options[0]
                    cid = winning_option.cid()
                    if cid.startswith('/ipfs/'):
                        cid = cid[6:]
                    score = question_results.get(cid, {}).get('score', 0)
                    if score is None:
                        score = 0
                        
                    results.append({
                        'text': winning_option.text if hasattr(winning_option, 'text') else str(winning_option.value) if hasattr(winning_option, 'value') else 'Unnamed Option',
                        'value': winning_option.value if hasattr(winning_option, 'value') else None,
                        'score': round(score * 100, 2)
                    })
                else:
                    results.append(None)
                        
            except Exception as e:
                logger.error(f"Failed to calculate results for question {question_index}: {str(e)}")
                full_results.append([])
                results.append(None)
        stats.calculation_time = time.time() - calculation_start
            
        # After calculating all results, update the state mapping if needed
        mapping = load_state_mapping()
        if state.hivemind_id:
            if state.hivemind_id not in mapping:
                mapping[state.hivemind_id] = {
                    "state_hash": state.cid(),  # Use state.cid() instead of input cid
                    "name": basic_info['issue']['name'],
                    "description": basic_info['issue']['description'],
                    "num_options": basic_info['num_options'],
                    "num_opinions": basic_info['num_opinions'],
                    "answer_type": basic_info['issue']['answer_type'],
                    "questions": basic_info['issue']['questions'],
                    "tags": basic_info['issue']['tags'],
                    "results": results
                }
                save_state_mapping(mapping)
                logger.info(f"Added new state mapping for {state.hivemind_id}")
            elif mapping[state.hivemind_id]["state_hash"] == state.cid():  # Compare with state.cid()
                # Only update results if this is the latest state we're tracking
                mapping[state.hivemind_id]["results"] = results
                save_state_mapping(mapping)
                logger.info(f"Updated results for latest state of {state.hivemind_id}")
            else:
                logger.info(f"Skipping state update for historical state {state.cid()} of {state.hivemind_id}")
        
        # Calculate total time
        stats.total_time = time.time() - stats.start_time
        
        # Log the final statistics
        log_state_stats(stats)
        log_stats_to_csv(stats)
        
        # Add statistics to response
        basic_info['stats'] = stats.to_dict()
        basic_info['results'] = full_results  # Use full results for the frontend
        basic_info['full_opinions'] = full_opinions
        
        logger.info(f"Completed loading state info with {len(options)} options and {basic_info['total_opinions']} opinions")
        return basic_info

    except Exception as e:
        logger.error(f"Error processing state {cid}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create_issue")
async def create_issue(issue: HivemindIssueCreate):
    """Create a new HivemindIssue and save it to IPFS."""
    try:
        def create_and_save():
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
                # Special handling for Bool type constraints
                if issue.answer_type == 'Bool' and 'choices' in issue.constraints:
                    # Extract the true/false labels from the choices array
                    true_label = issue.constraints['choices'][0] if len(issue.constraints['choices']) > 0 else 'True'
                    false_label = issue.constraints['choices'][1] if len(issue.constraints['choices']) > 1 else 'False'
                    
                    # Set constraints in the format expected by HivemindState.add_predefined_options
                    modified_constraints = {
                        'true_value': true_label,
                        'false_value': false_label
                    }
                    new_issue.set_constraints(modified_constraints)
                # Special handling for Image type constraints
                elif issue.answer_type == 'Image':
                    # Validate and prepare image constraints
                    image_constraints = {}
                    
                    # Handle formats
                    if 'formats' in issue.constraints and isinstance(issue.constraints['formats'], list):
                        image_constraints['formats'] = issue.constraints['formats']
                    
                    # Handle max_size
                    if 'max_size' in issue.constraints and isinstance(issue.constraints['max_size'], int):
                        image_constraints['max_size'] = issue.constraints['max_size']
                    
                    # Handle dimensions
                    if 'dimensions' in issue.constraints and isinstance(issue.constraints['dimensions'], dict):
                        dimensions = {}
                        if 'max_width' in issue.constraints['dimensions'] and isinstance(issue.constraints['dimensions']['max_width'], int):
                            dimensions['max_width'] = issue.constraints['dimensions']['max_width']
                        if 'max_height' in issue.constraints['dimensions'] and isinstance(issue.constraints['dimensions']['max_height'], int):
                            dimensions['max_height'] = issue.constraints['dimensions']['max_height']
                        
                        if dimensions:
                            image_constraints['dimensions'] = dimensions
                    
                    if image_constraints:
                        new_issue.set_constraints(image_constraints)
                # Special handling for Video type constraints
                elif issue.answer_type == 'Video':
                    # Validate and prepare video constraints
                    video_constraints = {}
                    
                    # Handle formats
                    if 'formats' in issue.constraints and isinstance(issue.constraints['formats'], list):
                        video_constraints['formats'] = issue.constraints['formats']
                    
                    # Handle max_size
                    if 'max_size' in issue.constraints and isinstance(issue.constraints['max_size'], int):
                        video_constraints['max_size'] = issue.constraints['max_size']
                    
                    # Handle max_duration
                    if 'max_duration' in issue.constraints and isinstance(issue.constraints['max_duration'], int):
                        video_constraints['max_duration'] = issue.constraints['max_duration']
                    
                    if video_constraints:
                        new_issue.set_constraints(video_constraints)
                else:
                    new_issue.set_constraints(issue.constraints)
            elif issue.answer_type == 'Bool':
                # Add default constraints for Bool type
                new_issue.set_constraints({
                    'true_value': 'True',
                    'false_value': 'False'
                })

            # Set restrictions if provided
            if issue.restrictions:
                new_issue.set_restrictions(issue.restrictions)

            logger.info(f"Created issue with name: {issue.name}, type: {issue.answer_type}")
            
            try:
                # Save issue to IPFS and get CID
                issue_cid = new_issue.save()
                logger.info(f"Saved issue to IPFS with CID: {issue_cid}")
                
                # Create initial state with the issue
                initial_state = HivemindState()
                initial_state.set_hivemind_issue(issue_cid)
                logger.info("Set hivemind issue in state")
                
                # Initialize options variable
                options = []
                
                # Add predefined options only for Bool type
                if issue.answer_type == 'Bool':
                    options = initial_state.add_predefined_options()
                    logger.info(f"Added predefined options: {options}")
                
                state_cid = initial_state.save()
                logger.info(f"Saved state to IPFS with CID: {state_cid}")
                
                # Save state mapping
                mapping = load_state_mapping()
                mapping[issue_cid] = {
                    "state_hash": state_cid,
                    "name": issue.name,
                    "description": issue.description,
                    "num_options": len(options),
                    "num_opinions": 0,
                    "answer_type": issue.answer_type,
                    "questions": issue.questions,
                    "tags": issue.tags,
                    "results": None
                }
                save_state_mapping(mapping)
                logger.info("Updated state mapping")
                
                return {"issue_cid": issue_cid, "state_cid": state_cid}
            except Exception as e:
                logger.error(f"Error in create_and_save: {str(e)}")
                raise

        # Run the creation and save operation in a thread
        result = await asyncio.to_thread(create_and_save)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Failed to create issue: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/options/add", response_class=HTMLResponse)
async def add_option_page(request: Request, hivemind_id: str):
    """Render the add option page."""
    try:
        # Load the hivemind issue to get answer type and constraints
        issue = await asyncio.to_thread(lambda: HivemindIssue(cid=hivemind_id))
        
        return templates.TemplateResponse(
            "add_option.html",
            {
                "request": request,
                "hivemind_id": hivemind_id,
                "issue": issue
            }
        )
    except Exception as e:
        logger.error(f"Error loading issue for add option page: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/options/create")
async def create_option(option: OptionCreate):
    """Create a new option for a hivemind issue."""
    try:
        logger.info(f"=== Starting option creation process ===")
        logger.info(f"Input parameters - hivemind_id: {option.hivemind_id}")
        logger.info(f"Input parameters - value: {option.value} (type: {type(option.value)})")
        logger.info(f"Input parameters - text: {option.text}")

        # Get the latest state for this hivemind
        mapping = load_state_mapping()
        if option.hivemind_id not in mapping:
            logger.error(f"No state found for hivemind_id: {option.hivemind_id}")
            logger.debug(f"Available hivemind IDs in mapping: {list(mapping.keys())}")
            raise HTTPException(status_code=404, detail="No state found for this hivemind ID")
            
        latest_state_cid = mapping[option.hivemind_id]["state_hash"]
        logger.info(f"Latest state CID: {latest_state_cid}")

        def create_and_save():
            try:
                # Load the current state and issue
                logger.info(f"Loading current state from CID: {latest_state_cid}")
                state = HivemindState(cid=latest_state_cid)
                logger.info(f"Current state loaded successfully")
                logger.info(f"State details - Number of options: {len(state.options)}")
                logger.info(f"State details - Number of opinions: {len(state.opinions[0]) if state.opinions else 0}")

                logger.info(f"Loading issue from CID: {option.hivemind_id}")
                issue = HivemindIssue(cid=option.hivemind_id)
                logger.info(f"Issue loaded successfully")
                logger.info(f"Issue details - Answer type: {issue.answer_type}")
                logger.info(f"Issue details - Constraints: {issue.constraints}")

                # Create the new option
                logger.info("Creating new option object...")
                new_option = HivemindOption()
                new_option.set_hivemind_issue(hivemind_issue_hash=option.hivemind_id)
                
                # Set the option value based on the answer type
                try:
                    if issue.answer_type == 'Integer':
                        logger.info(f"Converting value to integer: {option.value}")
                        new_option.value = int(option.value)
                    elif issue.answer_type == 'Float':
                        logger.info(f"Converting value to float: {option.value}")
                        new_option.value = float(option.value)
                    else:
                        logger.info(f"Using value as string: {option.value}")
                        new_option.value = str(option.value)
                except (ValueError, TypeError) as e:
                    logger.error(f"Failed to convert value to {issue.answer_type}: {str(e)}")
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid value format for answer type {issue.answer_type}: {str(e)}"
                    )
                    
                new_option.text = option.text or ''
                
                # Validate the option
                logger.info("Validating option...")
                try:
                    if not new_option.valid():
                        logger.error("Option validation failed")
                        raise HTTPException(status_code=400, detail="Option validation failed")
                    logger.info("Option validation successful")
                except Exception as e:
                    logger.error(f"Option validation error: {str(e)}")
                    raise HTTPException(status_code=400, detail=f"Option validation error: {str(e)}")

                # Save the option to IPFS
                logger.info("Saving new option to IPFS...")
                option_cid = new_option.save()
                logger.info(f"Option saved successfully with CID: {option_cid}")

                # Add the option to the state
                logger.info("Adding option to state...")
                current_time = int(time.time())
                state.add_option(timestamp=current_time, option_hash=option_cid)
                logger.info(f"Option added successfully. New number of options: {len(state.options)}")

                # Save the updated state
                logger.info("Saving updated state...")
                new_state_cid = state.save()
                logger.info(f"New state saved successfully with CID: {new_state_cid}")

                # Return the CIDs and metadata
                result = {
                    "option_cid": option_cid, 
                    "state_cid": new_state_cid,
                    "issue_name": issue.name,
                    "issue_description": issue.description,
                    "num_options": len(state.options),
                    "num_opinions": len(state.opinions[0]) if state.opinions else 0,
                    "answer_type": issue.answer_type,
                    "questions": issue.questions,
                    "tags": issue.tags
                }
                logger.info("Result metadata prepared successfully")
                return result

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Unexpected error in create_and_save: {str(e)}")
                logger.exception("Full traceback:")
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

        # Run the creation in a thread to avoid blocking
        logger.info("Running option creation in background thread...")
        result = await asyncio.to_thread(create_and_save)
        
        # Update the state mapping
        logger.info("Updating state mapping...")
        await update_state(StateHashUpdate(
            hivemind_id=option.hivemind_id,
            state_hash=result["state_cid"],
            name=result["issue_name"],
            description=result["issue_description"],
            num_options=result["num_options"],
            num_opinions=result["num_opinions"],
            answer_type=result["answer_type"],
            questions=result["questions"],
            tags=result["tags"]
        ))
        logger.info("State mapping updated successfully")
        
        logger.info("=== Option creation process completed successfully ===")
        return {
            "status": "success",
            "option_cid": result["option_cid"],
            "state_cid": result["state_cid"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_option: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/add_opinion")
async def add_opinion_page(request: Request, cid: str):
    """Render the add opinion page."""
    try:
        # Load the state to get issue details
        state = await asyncio.to_thread(lambda: HivemindState(cid=cid))
        issue = await asyncio.to_thread(lambda: HivemindIssue(cid=state.hivemind_id))
        
        # Load options
        options = []
        for option_hash in state.options:
            try:
                option = await asyncio.to_thread(lambda h=option_hash: HivemindOption(cid=h))
                options.append({
                    'cid': option_hash,
                    'value': option.value if hasattr(option, 'value') else None,
                    'text': option.text if hasattr(option, 'text') else None
                })
            except Exception as e:
                logger.error(f"Failed to load option {option_hash}: {str(e)}")
                options.append({
                    'cid': option_hash,
                    'value': None,
                    'text': f"Failed to load: {str(e)}"
                })
        
        return templates.TemplateResponse(
            "add_opinion.html",
            {
                "request": request,
                "state_cid": cid,
                "hivemind_id": state.hivemind_id,
                "issue_name": issue.name,
                "issue_description": issue.description,
                "questions": issue.questions,
                "options": options
            }
        )
    except Exception as e:
        logger.error(f"Error rendering add opinion page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test_ipfs")
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

@app.get("/api/latest_state/{hivemind_id}")
async def get_latest_state(hivemind_id: str):
    """Get the latest state hash for a given hivemind ID."""
    mapping = load_state_mapping()
    if hivemind_id not in mapping:
        raise HTTPException(status_code=404, detail="Hivemind ID not found")
    return {"hivemind_id": hivemind_id, **mapping[hivemind_id]}

@app.post("/api/update_state")
async def update_state(state_update: StateHashUpdate):
    """Update the state hash for a given hivemind ID."""
    mapping = load_state_mapping()
    state_file = STATES_DIR / f"{state_update.hivemind_id}.json"
    state_data = {
        "state_hash": state_update.state_hash,
        "name": state_update.name,
        "description": state_update.description,
        "num_options": state_update.num_options,
        "num_opinions": state_update.num_opinions,
        "answer_type": state_update.answer_type,
        "questions": state_update.questions,
        "tags": state_update.tags,
        "results": state_update.results
    }
    mapping[state_update.hivemind_id] = state_data
    try:
        with open(state_file, "w") as f:
            json.dump(state_data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save state file {state_file}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save state: {str(e)}")
    return {"status": "success", "hivemind_id": state_update.hivemind_id, **state_data}

@app.get("/api/all_states")
async def get_all_states():
    """Get all tracked hivemind states."""
    mapping = load_state_mapping()
    return {"states": [{"hivemind_id": k, **v} for k, v in mapping.items()]}

@app.post("/api/submit_opinion")
async def submit_opinion(opinion: OpinionCreate) -> Dict[str, Any]:
    """Submit a new opinion for a hivemind issue.
    
    Args:
        opinion: Opinion data including hivemind ID and ranking
        
    Returns:
        Dict containing success status and IPFS CID of saved opinion
    """
    try:
        def save_opinion():
            # Create opinion object
            hivemind_opinion = HivemindOpinion()
            hivemind_opinion.hivemind_id = opinion.hivemind_id
            hivemind_opinion.question_index = opinion.question_index
            
            # Create ranking from option list
            ranking = Ranking()
            ranking.set_fixed(opinion.ranking)
            hivemind_opinion.ranking = ranking.get()
            
            # Save and return CID
            return hivemind_opinion.save()
        
        # Execute the save operation in a thread
        cid = await asyncio.to_thread(save_opinion)
        
        return {
            "success": True,
            "cid": cid
        }
        
    except Exception as e:
        logger.error(f"Error submitting opinion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting opinion: {str(e)}"
        )

@app.get("/generate_keypair")
async def generate_keypair():
    """Generate a new Bitcoin keypair for signing opinions.
    
    Returns:
        dict: Contains private_key and address strings
    """
    private_key, address = generate_bitcoin_keypair()
    return {
        "private_key": str(private_key),
        "address": address
    }

@app.get("/validate_key/{private_key}")
async def validate_key(private_key: str):
    """Validate a Bitcoin private key and return its address.
    
    Args:
        private_key: WIF formatted private key
        
    Returns:
        dict: Contains valid status and address if valid
    """
    try:
        key = CBitcoinSecret(private_key)
        address = get_bitcoin_address(key)
        return {
            "valid": True,
            "address": address
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }

@app.post("/api/sign_opinion")
async def sign_opinion(request: Request):
    """Add a signed opinion to the hivemind state.
    
    Args:
        request: Raw request containing address, message, signature and data
        
    Returns:
        Dict indicating success status and any error message
    
    Raises:
        HTTPException: If the request data is invalid or signature verification fails
    """
    try:
        data = await request.json()
        
        # Extract required fields
        address = data.get('address')
        message = data.get('message')
        signature = data.get('signature')
        opinion_data = data.get('data')
        
        if not all([address, message, signature, opinion_data]):
            raise HTTPException(status_code=400, detail="Missing required fields")
            
        # Parse timestamp and state CID from message format: "timestampCID"
        try:
            # First 10 chars are timestamp, rest is CID
            timestamp_str = message[:10]
            opinion_hash = message[10:]
            timestamp = int(timestamp_str)
            logger.info(f"Parsed timestamp: {timestamp}, opinion_hash: {opinion_hash}")
        except ValueError:
            logger.error(f"Failed to parse message format: {message}")
            raise HTTPException(status_code=400, detail="Invalid message format")
            
        # Get hivemind state from the opinion data
        try:
            # First load the opinion to get its hivemind_id
            opinion = await asyncio.to_thread(lambda: HivemindOpinion(cid=opinion_hash))

            if not opinion.hivemind_id:
                raise HTTPException(status_code=400, detail="Opinion does not have an associated hivemind state")
                
            # Get the latest state hash from hivemind_states.json
            state_data = load_state_mapping().get(opinion.hivemind_id)
            if not state_data:
                raise HTTPException(status_code=400, detail="No state data found for hivemind ID")
            
            latest_state_hash = state_data["state_hash"]
            logger.info(f"Using latest state hash: {latest_state_hash}")
            
            # Use to_thread to run the synchronous HivemindState operations
            state = await asyncio.to_thread(lambda: HivemindState(cid=latest_state_hash))
            logger.info(f"Loaded state with CID: {opinion.hivemind_id}")
            
            # Verify the message signature before adding the opinion
            if not verify_message(message, address, signature):
                logger.error(f"Message verification failed for address {address}")
                raise HTTPException(status_code=400, detail="Signature is invalid")
            logger.info(f"signature ok")
            
            # Add the opinion using to_thread as well
            await asyncio.to_thread(
                lambda: state.add_opinion(
                    timestamp=timestamp,
                    opinion_hash=opinion_hash,
                    signature=signature,
                    address=address
                )
            )
            
            logger.info(f"Added opinion successfully")

            # Save the state using to_thread
            new_cid = await asyncio.to_thread(lambda: state.save())
            logger.info(f"Latest state CID: {new_cid}")
            
            # Calculate new results for the specific question
            logger.info("Calculating updated results...")
            def calc_results():
                return state.calculate_results(opinion.question_index)
            results = await asyncio.to_thread(calc_results)
            
            # Get sorted options to find the winner
            sorted_options = await asyncio.to_thread(lambda: state.get_sorted_options(question_index=opinion.question_index))
            
            # Format results with just the winning option
            formatted_results = []
            if sorted_options:
                winner = sorted_options[0]
                score = results.get(winner.cid().replace('/ipfs/', ''), {}).get('score', 0) or 0
                formatted_results.append({
                    'text': winner.text if hasattr(winner, 'text') else str(winner.value) if hasattr(winner, 'value') else '',
                    'value': winner.value if hasattr(winner, 'value') else '',
                    'score': round(score * 100, 2)
                })
            
            logger.info("Calculating updated results done")
            logger.info(f"New winning result for question {opinion.question_index}: {formatted_results}")
            
            # Update the state mapping with new state hash and metadata
            issue = await asyncio.to_thread(lambda: HivemindIssue(cid=opinion.hivemind_id))
            logger.info("Loading issue done")

            await update_state(StateHashUpdate(
                hivemind_id=opinion.hivemind_id,
                state_hash=new_cid,
                name=issue.name,
                description=issue.description,
                num_options=len(state.options),
                num_opinions=len(state.opinions[0]) if state.opinions else 0,
                answer_type=issue.answer_type,
                questions=issue.questions,
                tags=issue.tags,
                results=formatted_results
            ))
            logger.info("State mapping updated successfully")
            
            # Send notification to connected WebSocket clients
            if opinion_hash in active_connections:
                notification_data = {
                    "success": True,
                    "message": "Opinion signed successfully",
                    "opinion_hash": opinion_hash,
                    "state_cid": new_cid,
                    "results": formatted_results,
                    "hivemind_id": opinion.hivemind_id
                }
                for connection in active_connections[opinion_hash]:
                    try:
                        await connection.send_json(notification_data)
                    except Exception as e:
                        logger.error(f"Failed to send WebSocket notification: {str(e)}")
                        continue  # Skip failed connections
            
            return {
                "success": True,
                "cid": new_cid
            }
            
        except Exception as e:
            logger.error(f"Failed to process opinion: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
