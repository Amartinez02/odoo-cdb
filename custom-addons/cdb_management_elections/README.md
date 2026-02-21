# Church Elections Module for Casa de Bendición

This module adds a complete church elections system to the CDB Management module.

## Features

- **Contact Name Split**: First Name + Last Name fields with auto-concatenation
- **Elections Management**: Full lifecycle (Draft → Open → Closed → Published)
- **Position-based Voting**: Define positions/roles with configurable winner counts
- **Real-time Voting Board**: Live QWeb page with auto-updating vote counts
- **Published Results**: Formal results page with winner badges and totals
- **Vote Audit Log**: Every vote change is logged for transparency

## Installation

Install this module from the Odoo Apps menu. It depends on:
- `cdb_management`
- `bus` (for real-time updates)

## Usage

1. Go to **Church → Elections → Elections**
2. Create an election with positions and candidates
3. Click **Open Voting** to start
4. Add/subtract votes using the inline buttons
5. View the live board at `/cdb/elections/<id>`
6. Click **Close Voting** to compute winners
7. Click **Publish Results** to make the results page public

## License

LGPL-3
