from splunk_functions import splunk_query
from sourcetypes import sourcetypes
import os
import requests
import json
from datetime import datetime, timedelta
from tqdm import tqdm

SPLUNK_HOST="localhost"
SPLUNK_PORT="8089"

START_DATE = "07/31/2017:20:15:00" # Needs to be in American Splunk time format.
END_DATE = "08/31/2017:18:00:00" # Needs to be in American Splunk time format.
SPLUNK_TIME_FORMAT = '%m/%d/%Y:%H:%M:%S'

username=os.getenv('SPLUNK_UN')
password=os.getenv('SPLUNK_PW')

start_date = datetime.strptime(START_DATE, SPLUNK_TIME_FORMAT)
end_date = datetime.strptime(END_DATE, SPLUNK_TIME_FORMAT)

# Get list of sourcetypes. Limited to last day for speed
one_day = timedelta(days=7)
end_less_one = end_date - one_day

# The REST API endpoint URL
url = f'https://{SPLUNK_HOST}:{SPLUNK_PORT}/services/data/indexes?output_mode=json'

# Make a GET request to the Splunk REST API
response = requests.get(url, auth=(username, password), verify=False)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Extract the index names
    index_names = [entry['name'] for entry in data['entry']]

indices="\n".join(index_names)

index='botsv2'
source_types_list = sourcetypes.split(" ")
sourcetype = source_types_list[0]

splunk_data_dict = {}

for sourcetype in tqdm(source_types_list):
    fields = splunk_query(f"index={index} sourcetype={sourcetype}| fieldsummary | table field count", dataframe=True)
    total_rows = max(fields['count'])
    fields["coverage"] = round((fields['count'] / total_rows), 2)
    selected_cols = ['field', 'coverage']
    fields_dict = fields[selected_cols].to_dict(orient='records')
    splunk_data_dict[sourcetype] = fields_dict

splunk_json = json.dumps(splunk_data_dict)

with open(f"{index}_splunk_field.json", "w") as f:
    f.write(splunk_json)


