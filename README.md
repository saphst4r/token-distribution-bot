# HYB Distribution Tool

A tool for automating HYB token distribution to multiple addresses.

## Installation

1. Clone the repository:

```bash
git clone git@github.com:saphst4r/token-distribution-bot.git
cd token-distribution-bot
```

2. Run the setup script:

```bash
setup.bat
```

3. Start the web interface:

```bash
run_webui.bat
```

## Optional Configuration

### Private Key Setup

1. Rename `.env.example` to `.env`
2. Add your private key to the file:

```
PRIVATE_KEY=0x...
```

### Address List Setup

Add recipient addresses to `address_list.json`. Example format:

```json
{
  "addresses": [
    "0x1234567890123456789012345678901234567890",
    "0x2345678901234567890123456789012345678901",
    "0x3456789012345678901234567890123456789012"
  ]
}
```

## Disclaimer

⚠️ This tool has only been tested on testnet. Use at your own risk when using in mainnet.
