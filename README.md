# Arbor Messages Forwarder

## Overview
This script automates the process of logging into the Arbor portal, extracting school messages, and forwarding them to a specified email address.

## Setup
1. Ensure Python 3.10 is installed on your machine. Earlier or later versions of Python may or may not work.
2. Clone or download this script to your local machine.
3. Install the required Python packages by running `pip install -r requirements.txt`.
4. Rename `.env.template` to `.env` and update it with your Arbor credentials, the e-mail the messages will appear to have been sent from, and the forwarding email.

## Usage
Run the script with `python arbor_message_forwarder.py` from Cron. The script will automatically perform all its tasks in the background, and new messages should automatically appear in your forwarding e-mail inbox.

### Optionally use GPT-4 to add line breaks and a subject
The messages come as a single line, with no subject. Adding paragraph breaks and a subject line greatly improves readability. To enable this functionality, specify your OPENAI_API_KEY in the `.env` file.

## Note
On the first run, the script will attempt to install a version of the Chromium browser compatible with Pyppeteer (if it is not already installed).
