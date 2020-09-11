python collect_container_cpu.py &
sleep 60
for i in {1..31}
do
time python ui.py ETL &
sleep 120
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys

