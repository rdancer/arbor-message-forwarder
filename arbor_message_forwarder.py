# arbor_message_forwarder.py

import asyncio
from pyppeteer import launch
from pyppeteer import chromium_downloader
from dotenv import load_dotenv
import os
import aiosqlite
from insert_email import Gmail
import email.utils
from time import sleep
from datetime import datetime
from gippity import format_message

# Load environment variables
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASS_PHRASE = os.getenv("PASS_PHRASE")
FROM_EMAIL = os.getenv("FROM_EMAIL")
FORWARD_TO_EMAIL = os.getenv("FORWARD_TO_EMAIL")
DATABASE_PATH = os.getenv("DATABASE_PATH")
ASSUME_SKIP_OLD_MESSAGES = os.getenv("ASSUME_SKIP_OLD_MESSAGES") == "True"
DEBUG_HEADFUL = os.getenv("DEBUG_HEADFUL") == "True"

async def main():
    setup_pyppeteer()
    await setup_database()

    browser = await launch(options={'headless': not DEBUG_HEADFUL, 'args': ['--no-sandbox']})
    page = await browser.newPage()

    # Step 1: Login
    await page.goto('https://login.arbor.sc')
    await page.type('input[name="email"]', EMAIL)
    await page.type('input[name="password"]', PASS_PHRASE)
    # Simulate pressing Enter after typing in the password
    await page.keyboard.press('Enter')
    await page.waitForNavigation() # Will redirect to the school domain

    # Step 2: Navigate to the messages page
    # Extract the current domain from the page's URL
    current_url = page.url
    domain = current_url.split('?')[0]  # Removes query parameters if any

    # Specify the path to navigate to
    path = '/?/guardians/communication-center-ui/school-messages/'

    # Construct the full URL by combining the domain and the path
    target_url = f"{domain}{path}"

    # Navigate to the new URL
    await page.goto(target_url)

    # await page.waitForNavigation(waitUntil='networkidle0') # Wait for all content to load
    await asyncio.sleep(10) # Let UI settle

    # Step 3: Click on each message and extract details
    messages = await page.querySelectorAll('.mis-property-row')
    print(f"Found {len(messages)} messages")
   
    for i, message in enumerate(messages):
        if i > float('inf'):
            print(f"Reached message limit of {i} -- for debugging")
            break
        # Click on the message
        await message.click()
        # await page.waitForNavigation(waitUntil='networkidle0') # Wait for all content to load
        await asyncio.sleep(2) # Let UI settle

        # Extract headers
        header_texts = await page.evaluate('''() => {
            const elements = Array.from(document.querySelectorAll('.slideover-content .x-form-display-field-body-property-row'));
            return elements.map(element => element.innerText.trim());
        }''')

        if len(header_texts) >= 2:
            received, sent_by = header_texts
        else:
            raise Exception('Failed to extract message headers')

        # Extract message text
        # I think that there is only one .arbor-simple-text element, but in case there are many...
        message_texts = await page.evaluate('''() => {
            const elements = Array.from(document.querySelectorAll('.slideover-content .arbor-simple-text'));
            return elements.map(element => element.innerText.trim());
        }''')
        message_text = "\n".join(message_texts)

        # Store details in the database
        is_new = await store_message(received, sent_by, message_text)
        print(f"[{'new' if is_new else 'old'}] Message {i+1: 3d}/{len(messages)}: {received}, {sent_by}, {message_text}")
        if not is_new:
            print(f"Skipping {len(messages)-i-1} previously seen messages")
            break

        await page.click(".slideover-content button.arbor-cancel-button") # Close the message
        await asyncio.sleep(1) # Let UI settle

    await browser.close() # not really need to await, but do it anyway

    # Determine new messages and forward them
    await forward_new_messages()

async def store_message(received, sent_by, message_text):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute('''INSERT INTO messages (received, sent_by, message_text, forwarded)
              VALUES (?, ?, ?, 0)''', (received, sent_by, message_text))
            await db.commit()
            return True  # Message inserted successfully
        except aiosqlite.IntegrityError:
            # Duplicate entry, so the message is not inserted
            return False

async def forward_new_messages():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT received, sent_by, message_text FROM messages WHERE forwarded=0")
        messages = await cursor.fetchall()
        gmail = Gmail()    

        for received, sent_by, message_text in messages:
            # Construct the email body with received date and sender
            try:
                date = parse_custom_date_format(received, localtime=True)
            except Exception as e:
                print(f"Warning: Could not parse date {received}, substituting current time")
                date = email.utils.formatdate(localtime=True)
            subject, body = format_message(f"{message_text}")
            subject = f"Arbor message - {subject}"
            to_addr = FORWARD_TO_EMAIL
            from_name = sent_by.split("<")[0].strip()
            from_name_sanitized = "".join([c for c in from_name if c.isalpha() or c.isdigit() or c in "_-(). "]).rstrip()
            from_addr = f"{from_name_sanitized}<{FROM_EMAIL}>"  # This is the 'From' address for the email, set in .env
            
            # Use the Gmail class to insert the message
            gmail.insert_message(to_addr, from_addr, subject, body, date)
            
            # Update the database to mark the message as forwarded
            await db.execute("UPDATE messages SET forwarded=1 WHERE received=? AND sent_by=? AND message_text=?", (received, sent_by, message_text))
            await db.commit()
        # del gmail

def setup_pyppeteer():
    print('Checking if Chromium is downloaded...')

    # Check if Chromium is already downloaded
    if not chromium_downloader.check_chromium():
        print('Chromium is not downloaded. Downloading...')
        # Download Chromium
        chromium_downloader.download_chromium()
        print('Chromium downloaded.')

async def setup_database():
    if not os.path.exists(DATABASE_PATH):
        print(f"Creating SQLite database at {DATABASE_PATH}")
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS messages
                 (received TEXT, sent_by TEXT, message_text TEXT, forwarded INTEGER,
                 UNIQUE(received, sent_by, message_text))''')
            await db.commit()
        print("Database created.")
    else:
        print(f"Using existing SQLite database at {DATABASE_PATH}")

import email.utils
from datetime import datetime

def parse_custom_date_format(date_str: str, localtime=False) -> str:
    """
    Parses ther Arbor date format and returns the same date in a RFC-2822 format.
     
    Example:
       "02 March 2024, 12:00" -> "Sat, 02 Mar 2024 12:00:00 -0000"

    Args:
        date_str (str): The date string in a non-standard format, e.g., "12 March 2024, 12:00".
    
    Returns:
        str: The date string in RFC-2822 format.
    """
    try:
        dt = datetime.strptime(date_str, "%d %B %Y, %H:%M")
        standardized_date = dt.strftime("%a, %d %b %Y %H:%M:%S -0000")
        parsed_date = email.utils.parsedate_tz(standardized_date)
        timestamp = email.utils.mktime_tz(parsed_date)
        formatted_date = email.utils.formatdate(timestamp, localtime=localtime)
        return formatted_date
    except ValueError as e:
        raise ValueError(f"Error parsing date: {e}")
        return None

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
