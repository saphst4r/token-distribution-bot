# HYB Distribution Tool

This tool automates the distribution of HYB tokens to specified addresses.

## Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)

## Setup

1. Rename `.env.example` to `.env` and add your private key:

```
PRIVATE_KEY=your_private_key_here  # Include the 0x prefix
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The tool provides two interfaces:

1. Command Line Interface:

```bash
python tx_scheduler.py
```

2. Web Interface:

```bash
python webui.py
```

Then open http://localhost:5000 in your browser.

## Features

- Distribute HYB tokens to multiple addresses
- Configure distribution amount, interval, and duration
- Support for random recipient selection
- Real-time status monitoring and logging
- Optional "always include" address for each distribution round

## Note

Make sure to keep your private key secure and never share it with anyone. The tool supports loading the private key from the `.env` file or entering it directly in the web interface.
