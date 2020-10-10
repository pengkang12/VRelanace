rm /tmp/bo.log 
rm /tmp/bo_cpulimit.txt 
rm /tmp/kube-cpu.txt 
rm /tmp/skopt_input_ETLTopologySys.txt 
rm /tmp/skopt_input_IoTPredictionTopologySYS.txt
rm /tmp/skopt_model_ETLTopologySys
rm /tmp/skopt_model_IoTPredictionTopologySYS
echo "0, 10" > /tmp/window_ETLTopologySys.txt
echo "0, 10" > /tmp/window_IoTPredictionTopologySYS.txt


touch /tmp/bo_cpulimit.txt

python collect_container_cpu.py &
bash script/redis-data.sh
sleep 120
for i in {1..61}
do
python collect_container_cpu.py &
python ui.py ETL &
python ui.py IoT &
sleep 30
python BO/bayesian_optimization.py >> /tmp/bo.log
sleep 90
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys

