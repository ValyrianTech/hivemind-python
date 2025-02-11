# Hivemind Insights

A web application for visualizing Hivemind states stored on IPFS.

## Features

- Simple, clean interface for viewing Hivemind states
- Real-time loading of IPFS state data
- Visual representation of voting results
- Detailed view of issues, questions, and rankings
- Responsive design that works on all devices

## Installation

1. Install the requirements:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python -m flask run
```

3. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Enter an IPFS hash of a HivemindState in the input field
2. Click "Load" to fetch and display the state
3. View the overview statistics and detailed information for each issue

## Technologies Used

- Backend: Flask
- Frontend: HTML5, CSS3, JavaScript
- Styling: TailwindCSS
- Dependencies: hivemind-python, ipfs-dict-chain
