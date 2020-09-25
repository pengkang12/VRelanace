rm /tmp/skopt.model 
rm /tmp/bo.log 
rm /tmp/bo_cpulimit.txt 
rm /tmp/kube-cpu.txt 
rm /tmp/skopt_input_ETLTopologySys.txt 
touch /tmp/bo_cpulimit.txt


python collect_container_cpu.py &
sleep 120
for i in {1..121}
do
python collect_container_cpu.py &
python ui.py ETL &
python ui.py IoT &
sleep 30
python BO/hill_climbing.py >> /tmp/bo.log
sleep 90
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys

