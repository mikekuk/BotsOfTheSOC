import dotenv
from datetime import datetime, timedelta
from splunk_functions import splunk_query

dotenv.load_dotenv(".env")

START_DATE = "07/31/2017:20:15:00" # Needs to be in American Splunk time format.
END_DATE = "08/31/2017:18:00:00" # Needs to be in American Splunk time format.
SPLUNK_TIME_FORMAT = '%m/%d/%Y:%H:%M:%S'


start_date = datetime.strptime(START_DATE, SPLUNK_TIME_FORMAT)
end_date = datetime.strptime(END_DATE, SPLUNK_TIME_FORMAT)

# Get list of sourcetypes. Limited to last day for speed
one_day = timedelta(days=1)
end_less_one = end_date - one_day

sourcetypes = "MSAD:NT6:Health MSAD:NT6:SiteInfo Perfmon:CPU Perfmon:LogicalDisk Perfmon:Memory Perfmon:NTDS Perfmon:Network Perfmon:Network_Interface Perfmon:PhysicalDisk Perfmon:Process Perfmon:Processor Perfmon:System Powershell:ScriptExecutionSummary Script:ListeningPorts Unix:ListeningPorts Unix:UserAccounts WinHostMon WinRegistry access_combined apache:error apache_error auditd bandwidth collectd cpu csp-violation df interfaces iostat lastlog linux_audit linux_secure mysql:connection:stats mysql:instance:stats mysql:server:stats mysql:status mysql:tableStatus mysql:table_io_waits_summary_by_index_usage mysql:transaction:details mysql:transaction:stats mysql:variables netstat openPorts osquery_info osquery_results osquery_warning package pan:system pan:traffic protocol ps stream:arp stream:dhcp stream:dns stream:http stream:icmp stream:ip stream:ldap stream:mysql stream:smb stream:smtp stream:tcp stream:udp suricata symantec:ep:agent:file symantec:ep:agt_system:file symantec:ep:packet:file symantec:ep:traffic:file syslog top vmstat web_ping who wineventlog xmlwineventlog"

if __name__ == "__main__":
    sourcetypes = splunk_query("index=botsv2 | stats values(sourcetype)", earliest_time=end_less_one.isoformat(), latest_time=end_date.isoformat()).split('\n0')[-1]
    print(sourcetypes)