rm /tmp/skopt.model 
rm /tmp/bo.log 
rm /tmp/bo_cpulimit.txt 
rm /tmp/kube-cpu.txt 
rm /tmp/skopt_input_ETLTopologySys.txt 

python collect_container_cpu.py &
sleep 120
for i in {1..61}
do
python collect_container_cpu.py &
python ui.py ETL &
python ui.py IoT &
sleep 35
python BO/bayesian_optimization.py >> /tmp/bo.log
sleep 85
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys

