import imaplib
import email
from email.header import Header
from email.message import EmailMessage
from email.utils import formatdate
import dotenv # pip install python-dotenv
import os
import sys

# Load environment variables from the .env file
dotenv.load_dotenv()

class Gmail:
    def __init__(self):
        """
        Initializes the Gmail class.

        Raises:
        Exception: If the connection to the Gmail IMAP server fails.
        """
        # Gmail IMAP settings
        imap_host = os.getenv('IMAP_HOST')
        imap_user = os.getenv('IMAP_USER')
        imap_pass = os.getenv('IMAP_PASS_PHRASE')
        # Lazy connect, because most of the time, we don't actually have anything to forward
        self.mail = None

    def connect(self):
        try:
            # Connect to the Gmail IMAP server
            self.mail = imaplib.IMAP4_SSL(imap_host)
            # Login to the Gmail IMAP server
            self.mail.login(imap_user, imap_pass)
            print(f'Logged in successfully into {imap_host} as {imap_user}')
        except Exception as e:
            print(f'Failed to connect to {imap_host} as {imap_user}')
            print(e)
            raise

    def insert_message(self, to_addr, from_addr, subject, body, date=None):
        """
        Inserts a message into the inbox of the Gmail account.

        Args:
        to_addr (str): The email address of the recipient.
        from_addr (str): The email address of the sender.
        subject (str): The subject of the message.
        body (str): The body of the message.
        date (str): The timestamp of the message. Defaults to the current timestamp.
        """
        if not self.mail:
            self.connect()
        # Create a new message (MIME format)
        msg = EmailMessage()
        msg['To'] = to_addr
        msg['From'] = from_addr
        msg['Subject'] = subject
        msg['Date'] = date or formatdate(localtime=True)
        msg.set_content(body)

        # Convert the message to a string and then to bytes
        message = msg.as_bytes()

        # Select the mailbox you want to insert into, in this case, the inbox
        self.mail.select('inbox')

        # Append the message to the selected mailbox
        status, _ = self.mail.append('inbox', '', imaplib.Time2Internaldate(email.utils.mktime_tz(email.utils.parsedate_tz(msg['Date']))), message)
        if status != 'OK':
            raise Exception(f"Failed to insert message: {status}")
        else:
            print(f'Inserted message into inbox: to: {to_addr} from: {from_addr} subject: {subject} body: {body}')

    def close(self):
        try:
            self.mail.logout()
            print('Gmail: Logged out.')
        except Exception as e:
            print(f'Gmail: Error logging out.')
            raise

    def __del__(self):
        if self.mail:
            self.close()