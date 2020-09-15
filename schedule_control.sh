rm /tmp/skopt.model 
rm /tmp/bo.log 
rm /tmp/bo_cpulimit.txt 
rm /tmp/kube-cpu.txt 
rm /tmp/skopt_input_ETLTopologySys.txt 

python collect_container_cpu.py &
sleep 120
for i in {1..121}
do
python ui.py ETL &
sleep 120
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys

