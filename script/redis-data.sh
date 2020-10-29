redis-cli -h master flushall
redis-cli -h master set ETLTopologySys_1595026084367_MSGID_1117003576802 1
redis-cli -h master set ETLTopologySys_1595026114367_MSGID_1117003576803 1
redis-cli -h master hset ETLTopologySys_sink 1117003576802 1595026134378
redis-cli -h master hset ETLTopologySys_sink 1117003576803 1595026134383
redis-cli -h master keys ETL*
redis-cli -h master hkeys ETLTopologySys_sink

