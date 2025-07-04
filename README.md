# Arbor Message Forwarder<br />🌳 ➡️ 📧

## Overview
This script automates the process of logging into the Arbor portal, extracting school messages, and forwarding them to a specified email address.

### Optionally use GPT-4 to add line breaks and a subject
The messages come as a single run-on line, and there is no subject. Adding paragraph breaks and a subject line greatly improves readability. To enable, specify your OPENAI_API_KEY in the `.env` file.

## Requirements

- [Arbor](https://login.arbor.sc/) account
- E-mail account with IMAP access
- (optionally) [OpenAI API key](https://platform.openai.com/api-keys)

## Setup
1. Ensure Python 3.10 is installed on your machine. Earlier or later versions of Python may or may not work.
2. Clone or download this script to your local machine.
3. Install the required Python packages by running `pip install -r requirements.txt`.
4. Rename `.env.template` to `.env` and update it with your Arbor, IMAP, and (optionally) OpenAI credentials, the e-mail the messages will appear to have been sent from, and the forwarding email.
5. If the *Arbor* portal is not in the same timezone, set `ARBOR_TIMEZONE` in the `.env` file (e.g. `Europe/London`).

## Usage
Run the script with `python arbor_message_forwarder.py` from Cron. The script will automatically perform all its tasks in the background, and new messages should automatically appear in your forwarding e-mail inbox.

The messages are automatically labelled with the label `Arbor` (configurable in the `.env` file), so you can easily find them in your inbox, or filter/forward them. Alternatively, you can automacially add a prefix to the subjects of the messages.

## Note
On the first run, the script will attempt to install a version of the Chromium browser compatible with Pyppeteer (if it is not already installed).

### Troubleshooting

(OS X only) If you want to run from `cron` periodically (recommended), go to *System Settings > Privacy & Security > Full Disk Access*, and add `/usr/sbin/cron` to the list, then either restart the computer, or run the following commands from the terminal:

```
sudo launchctl stop com.apple.periodic-daily
sudo launchctl start com.apple.periodic-daily
```
