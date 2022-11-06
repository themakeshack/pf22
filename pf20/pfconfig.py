def init():
    global lastFeed
    global lcd_line_2


# Some switches to turn on or off to change program behavior
DEBUG = True  # Turns debugging on/off
DEBUGLEVEL = 0  # Sets a debug level. Only messages at or higher than this level will be displayed
MOTORON = True  # Enables or disables the motor - useful while debugging
CHUCKNORRIS = False  # Turns on/off Chuck Norris jokes in email replies
NUMBERTRIVIA = True  # Turns on/off Numers Trivia in email replies

# Files that we care about
LOGFILE = "/tmp/petfeeder.log"  # General purpose log file
PICFILE = "/tmp/picfile.jpg"  # This is where the camera saves the picture
SPSHEET = "Pet Feeder"  # Google spreadsheet name

#Email Info
GMAIL_KEYWORDS = ['FEED', 'PIC',
                  'STATUS']  # Subject keywords the system will respond to; add keyword to processKeyword()

GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/gmail.labels',
          'https://www.googleapis.com/auth/gmail.compose'
          ]
EMAIL_FROM = 'feedlucky@gmail.com'
VOICE_EMAIL="ifttt.com"
MAILCHECK_INTERVAL=30
ATTACHMENT_DIR = "/tmp/"
ATTACHMENT_FILE = "picfile.jpg"
API_ENDPOINT = "http://localhost:5000"

# Google Sheets Info
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
PF_SPREADSHEET_ID='1Qh195iKy-CbU1W033cu8QiK3cUfUwmVorvBgNB2_XXg'
PF_SPREADSHEET_RANGE_NAME='PETFEEDER_LOG!A1:C'

# GPIO pins for feeder control
MOTORCONTROLPIN = 19
FEEDBUTTONPIN = 6
RESETBUTTONPIN = 12

# GPIO pin for LED light
LEDLIGHT = 4

# Variables for feeding information
READYTOFEED = False
FEEDINTERVAL = 28800  # 28800  # This translates to 8 hours in seconds
FEEDFILE = "/home/pi/pf20/data/lastFeed"
CUPSTOFEED: int = 1
MOTORTIME = CUPSTOFEED * 30  # It takes 23 seconds of motor turning (~1.75 rotations) to get 1 cup of feed
