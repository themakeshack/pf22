from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pfconfig import SHEETS_SCOPES, PF_SPREADSHEET_ID, PF_SPREADSHEET_RANGE_NAME
from datetime import datetime
from my_debug import printdebug

def update_sheet(input_method):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SHEETS_SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=PF_SPREADSHEET_ID,
                                range=PF_SPREADSHEET_RANGE_NAME).execute()
    values = result.get('values', [])

    printdebug( 1, 'The spreadsheet has ' + str(len(values)) + ' rows')
    printdebug(1, values )
    if not values:
        printdebug(1, 'No data found.')
    else:
        for row in values:
            # Print columns A and C, which correspond to indices 0 and 2.
            if len(row) > 0:
                printdebug(1, '%s, %s' % (row[0], row[2]))
    d = datetime.now()
    TODAY_DATE = d.strftime("%b %d, %Y")
    TIME_NOW = d.strftime("%I:%M:%S %p")
    values = [
        [
          TODAY_DATE, TIME_NOW, input_method
        ],
    ]

    body = {
        'values': values
    }

    value_input_option='RAW'

    result = sheet.values().append(
        spreadsheetId=PF_SPREADSHEET_ID, range=PF_SPREADSHEET_RANGE_NAME,
        valueInputOption=value_input_option, body=body).execute()
    printdebug(1, '{0} cells appended.'.format(result \
                                    .get('updates') \
                                    .get('updatedCells')))

if __name__ == '__main__':
    update_sheet("input_method")