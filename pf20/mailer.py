import base64
import mimetypes
import os
import re
import socket
import time
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import urllib3
from apiclient import errors
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# Local imports
from my_debug import printdebug
from pfconfig import GMAIL_SCOPES, API_ENDPOINT, GMAIL_KEYWORDS, EMAIL_FROM, VOICE_EMAIL


def have_internet():
    # Check if our internat connection is working
    try:
        # connect to www.google.com to see if internet is accessible
        socket.create_connection(("www.google.com", 80))
        printdebug(1, "Internet is accessible")
        return True
    except OSError:
        pass
    printdebug(1, "Internet is not accessible")
    return False


def openmail():
    # Setup a mail service object
    try:
        store = file.Storage('token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('credentials.json', GMAIL_SCOPES)
            creds = tools.run_flow(flow, store)
        service = build('gmail', 'v1', http=creds.authorize(Http()))
        return (service)
    except:
        printdebug(1, "Could not open gmail service")


def processKeyword(keyword, email_to, input_method):
    # Construct and make API calls for keywords
    # Open a pool manager for making our API request
    http = urllib3.PoolManager()
    API_URL = API_ENDPOINT + "/" + keyword
    data = {'email_to': email_to, 'input_method' : input_method}
    http.request('GET', API_URL, data)
    return ()


def checkmail():
    # Call the mail service and check for keywords
    # Call the Gmail API to fetch INBOX
    service = openmail()
    printdebug(1, "Inside checkmail and opened the service")

    # Initialize a few local variables
    mail_result = {}  # mail_result stores the results by keyword
    messages = {}  # messages store the messages by keyword
    sender = ""

    for keyword in GMAIL_KEYWORDS:
        query_string = 'is:unread subject:\"' + keyword + '\"'  # create the query string to take in only unread messages with the subject <keyword>
        mail_result[keyword] = service.users().messages().list(userId='me', labelIds=['INBOX'],
                                                               q=query_string).execute()
        messages[keyword] = mail_result[keyword].get('messages', [])
        printdebug(1, "Inside checkmail - did the service query")
        if not messages[keyword]:
            printdebug(1, "No messages with subject %s found." % keyword)
        else:
            for message in messages[keyword]:

                # Make message UNREAD
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                msg_labels = CreateMsgLabels()  # create new message label without UNREAD
                modmsg = service.users().messages().modify(userId='me', id=message['id'],
                                                           body=msg_labels).execute()  # Remove the UNREAD label from message

                # Extract the sender's email ID and store it in email_to
                payload_headers = msg['payload'][
                    'headers']  # This gives a bunch of key:value pairs one of which is {'name':'From', 'value':'sender string'}
                for kvpair in payload_headers:
                    if kvpair['name'] == 'From':  # Look for the 'name': 'From'
                        sender = kvpair['value']  # and get the sender value
                email_id_string = re.findall('\S+@\S+', sender)  # Remove the sender's name from the string
                email_to = email_id_string[0][1:len(
                    email_id_string[0]) - 1]  # chop the leading '<' and the trailing '>' to extract the email ID

                # Process the action for the keyword, if the email_to hs IFTTT that is a voice command
                if VOICE_EMAIL in email_to:
                    processKeyword(keyword, EMAIL_FROM, "voice" )
                else:
                    processKeyword(keyword, email_to, "email")


def CreateMsgLabels():
    """Create object to update labels.

    Returns:
      A label update object.
    """
    return {'removeLabelIds': ['UNREAD'], 'addLabelIds': []}


def SendMessage(sender, to, subject, message_text, file_dir=None, filename=None):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message.
      :param filename:
      :param file_dir:
      :param message_text:
      :param subject:
      :param to:
      :param sender:
    """
    user_id = 'me'

    try:
        if file_dir is None:
            message = CreateMessage(sender, to, subject, message_text)
        else:
            message = CreateMessageWithAttachment(sender, to, subject, message_text, file_dir, filename)
        service = openmail()
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        printdebug(1, 'Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        printdebug(1, 'An error occurred: %s' % error)


def CreateMessage(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode('UTF-8')).decode('ascii')}


def CreateMessageWithAttachment(sender, to, subject, message_text, file_dir,
                                filename):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.
      file_dir: The directory containing the file to be attached.
      filename: The name of the file to be attached.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text)
    message.attach(msg)

    path = os.path.join(file_dir, filename)
    content_type, encoding = mimetypes.guess_type(path)
    if os.path.isfile(file_dir + '/' + filename):
        pass
    else:
        printdebug(1, "attachment file, " + path + " ,cannot be found")
        return

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(path, 'rb')
        msg = MIMEText(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(path, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(path, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(path, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()

    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_string().encode('UTF-8')).decode('ascii')}


if __name__ == "__main__":
    printdebug(1, "Starting checkmail")
    while True:
        if have_internet():
            checkmail()
            time.sleep(1)
