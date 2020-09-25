redis-cli -h master flushall
redis-cli -h master set ETLTopologySys_1595026084367_MSGID_1117003576800 1
redis-cli -h master set ETLTopologySys_1595026134367_MSGID_1117003576801 1
redis-cli -h master set ETLTopologySys_1595026084367_MSGID_1117003576802 1
redis-cli -h master set ETLTopologySys_1595026114367_MSGID_1117003576803 1
redis-cli -h master set ETLTopologySys_1595026134367_MSGID_1117003576804 1
redis-cli -h master set ETLTopologySys_1595026134367_MSGID_1117003576805 1
redis-cli -h master set ETLTopologySys_1595026134367_MSGID_1117003576806 1
redis-cli -h master set ETLTopologySys_1595026134367_MSGID_1117003576807 1
redis-cli -h master set ETLTopologySys_1595026134367_MSGID_1117003576808 1
redis-cli -h master set ETLTopologySys_1595026134367_MSGID_1117003576809 1
redis-cli -h master hset ETLTopologySys_sink 1117003576802 1595026134378
redis-cli -h master hset ETLTopologySys_sink 1117003576795 1595026134379
redis-cli -h master hset ETLTopologySys_sink 1117003576799 1595026134381
redis-cli -h master hset ETLTopologySys_sink 1117003576804 1595026134382
redis-cli -h master hset ETLTopologySys_sink 1117003576805 1595026134383
redis-cli -h master hset ETLTopologySys_sink 1117003576806 1595026134383
redis-cli -h master hset ETLTopologySys_sink 1117003576803 1595026134383
redis-cli -h master hset ETLTopologySys_sink 1117003576807 1595026134383
redis-cli -h master hset ETLTopologySys_sink 1117003576808 1595026134383
redis-cli -h master hset ETLTopologySys_sink 1117003576809 1595026134384
redis-cli -h master keys ETL*
redis-cli -h master hkeys ETLTopologySys_sink

