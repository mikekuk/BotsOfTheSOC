SERIES = 0
SEED = 42
RUN_NAME = "GPT4o"
TEMPERATURE = 0.4

INDEX = "botsv2"
START_DATE = "07/31/2017:00:10:00"
END_DATE = "08/31/2017:23:59:59"
SPLUNK_TIME_FORMAT = '%m/%d/%Y:%H:%M:%S'
SPLUNK_HOST="localhost"
SPLUNK_PORT="8089"
MAX_CHAR_RETURN = 100000 # Sets the target max number of chars to return from Splunk for log results. This only effects results that exceed the max row count.
MAX_ROW_RETURN = 500 # Sets the max number of rows to return from Splunk
QUESTIONS = 'Questions.json'
LOG = 'log.csv'
MODEL = "gpt-4o"
ROUNDS = 15
CLEAR_HISTORY = False