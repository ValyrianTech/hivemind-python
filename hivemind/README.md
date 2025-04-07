# Hivemind Web Application

This directory contains a web application implementation of the Hivemind Protocol, providing a user-friendly interface for creating and participating in decentralized decision-making processes.

## Overview

The Hivemind web application allows users to:
- Create new hivemind issues with customizable questions and constraints
- Submit options for consideration
- Vote on options using various ranking methods
- View real-time results and consensus
- Participate in a fully decentralized decision-making process

## Architecture

The application is built with:
- FastAPI for the backend API and WebSocket support
- Jinja2 templates for server-side rendering
- JavaScript for interactive frontend features
- IPFS for decentralized data storage
- Bitcoin message signing for cryptographic verification

## Dependencies

### BitcoinMessageSigner

The web application requires [BitcoinMessageSigner](https://github.com/ValyrianTech/BitcoinMessageSigner) for cryptographic verification of user actions. This mobile application allows users to:

- Scan QR codes displayed in the web interface
- Sign opinions (votes) using Bitcoin's message signing capabilities
- Sign when submitting new options
- Sign when updating participant names
- Sign when selecting consensus outcomes

All actions in the Hivemind Protocol are authenticated and verified through these cryptographic signatures, ensuring the integrity and security of the decision-making process.

## Running the Application

To run the web application:

```bash
cd hivemind
pip install -r requirements.txt
python app.py
```

The application will be available at http://localhost:8000 by default.

## Directory Structure

- `app.py`: Main application entry point and API routes
- `websocket_handlers.py`: WebSocket implementation for real-time updates
- `templates/`: Jinja2 HTML templates
- `static/`: Static assets (CSS, JavaScript, images)
- `states/`: Directory for storing hivemind state files
- `data/`: Directory for additional data files
- `logs/`: Application logs

## Usage

1. Access the web interface in your browser
2. Create a new hivemind issue or join an existing one
3. Install the BitcoinMessageSigner app on your mobile device
4. Scan QR codes to sign your actions
5. Participate in the decision-making process
6. View real-time results and consensus
