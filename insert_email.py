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

        """
        # Lazy connect, because most of the time, we don't actually have anything to forward
        self.mail = None

    def connect(self):
        """
        Raises:
        Exception: If the connection to the Gmail IMAP server fails.
        """
        # Gmail IMAP settings
        imap_host = os.getenv('IMAP_HOST')
        imap_user = os.getenv('IMAP_USER')
        imap_pass = os.getenv('IMAP_PASS_PHRASE')
        try:
            # Connect to the Gmail IMAP server
            self.mail = imaplib.IMAP4_SSL(imap_host)
            if os.getenv('DEBUG'):
                # set internal debugging flags for imaplib
                # note that __debug__ must also be True, which in practice means we are not running the python interpreter in optimized mode (i.e. not using -O or -OO flags)
                self.mail.debug = 4
            # Login to the Gmail IMAP server
            self.mail.login(imap_user, imap_pass)
            print(f'Logged in successfully into {imap_host} as {imap_user}')
        except Exception as e:
            print(f'Failed to connect to {imap_host} as {imap_user}')
            print(e)
            raise

    def insert_message(self, to_addr, from_addr, subject, body, date=None, gmail_labels=[]):
        """
        Inserts a message into the inbox of the Gmail account.

        Args:
        to_addr (str): The email address of the recipient.
        from_addr (str): The email address of the sender.
        subject (str): The subject of the message.
        body (str): The body of the message.
        date (str): The timestamp of the message. Defaults to the current timestamp.
        gmail_labels (list[str]): A list of labels to apply to the message. Defaults to an empty list. Only GMail is supported. Attempting to set labels with other IMAP providers may be a no-op, or it may result in an error.
        """
        if self.mail is None:
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
        
        # Apply the labels to the message
        # XXX TODO this should be done using IMAPClient:
        # ```python
        # from imapclient import IMAPClient
        # with IMAPClient('imap.gmail.com', ssl=True) as server:
        #     server.login(user, pw)
        #     server.select_folder('INBOX')
        #     # Append the message
        #     msg_uid = server.append('INBOX', message, flags=None, msg_time=msg_date)
        #     # Then label it in one shot:
        #     server.add_gmail_labels(msg_uid, ['Arbor', 'Foo Bar'])
        # ```
        try:
            code, resp = self.mail.response('APPENDUID')
            if code != 'APPENDUID':
                raise Exception(f"Failed to get APPENDUID: {code}")
            uidvalidity_str, new_uid = resp[0].decode().split() # new_uid='123456'
        except Exception as e:
            print(f"Failed to get appended message UID from the Gmail IMAP service -- {e.__class__.__name__}: {e}")
            raise
        self.apply_labels(new_uid, gmail_labels)

        print(f'Inserted message into inbox: to: {to_addr} from: {from_addr} labels: {gmail_labels} subject: {subject} body: {body}')
        
    def apply_labels(self, message_uid: str, labels: list[str] = []) -> None:
        """
        Applies labels to a message in the Gmail inbox.

        The label(s) are automatically created by Gmail if they do not already exist. (The way it works, labels are sort of auto-created folders -- the labels are created as soon as the first message is labeled with them. Then even if a label is removed from all messages, i.e. there are no more messages with that label, the label still persists in the UI. This is somewhat confusing conceptually, but from the user perspective it follows the least surprise principle.)

        Args:
        message_uid (str): The unique ID of the message to apply labels to. Note: this is an IMAP UID, not the message ID.
        labels (list[str]): A list of labels to apply to the message -- if empty or not provided, no labels are applied.
        Raises:
        RuntimeError: If the message with the given ID is not found or if the labels cannot be applied.
        """
        labels = [lbl.strip() for lbl in labels if lbl and lbl.strip()]  # Remove empty or whitespace-only labels
        if not labels:
            if os.getenv('DEBUG'):
                print(f'No or empty labels provided for message UID {message_uid} -- {labels=}')
            return
        # Apply Gmail labels via STORE
        quoted = ' '.join(f'"{lbl}"' for lbl in labels)
        flags_literal = f'({quoted})'
        status, _ = self.mail.uid("STORE", message_uid, "+X-GM-LABELS", flags_literal)
        if status != 'OK':
            raise RuntimeError(f"Failed to apply labels {quoted} to message UID {message_uid}: {status}")
        if os.getenv('DEBUG'):
            print(f'Applied labels {quoted} to message UID {message_uid}')

    def close(self):
        try:
            self.mail.logout()
            self.mail = None
            print('Gmail: Logged out.')
        except Exception as e:
            print(f'Gmail: Error logging out.')
            raise

    def __del__(self):
        if self.mail:
            self.close()