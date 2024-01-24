SERIES = 1
SEED = 2
RUN_NAME = "single_agent_2024-01-24"

INDEX = "botsv2"
START_DATE = "07/31/2017:20:15:00"
END_DATE = "08/31/2017:18:00:00"
SPLUNK_TIME_FORMAT = '%m/%d/%Y:%H:%M:%S'
SPLUNK_HOST="localhost"
SPLUNK_PORT="8089"
MAX_CHAR_RETURN = 30000 # Sets the target max number of chars to return from Splunk for log results. This only effects results that exceed the max row count.
MAX_ROW_RETURN = 200 # Sets the max number of rows to return from Splunk
QUESTIONS = 'Questions.json'
LOG = 'log.csv'
MODEL = "gpt-4-1106-preview"
ROUNDS = 20