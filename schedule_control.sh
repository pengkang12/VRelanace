rm /tmp/bo.log 
rm /tmp/bo_*
rm /tmp/kube-cpu.txt 
rm /tmp/skopt_*
echo "0, 10" > /tmp/window_ETLTopologySys.txt
echo "0, 10" > /tmp/window_IoTPredictionTopologySYS.txt


bash script/redis-data.sh

python collect_container_cpu.py &
sleep 120
for i in {1..321}
do
python collect_container_cpu.py &
python ui.py ETL &
python ui.py IoT &
sleep 30
python BO/bayesian_optimization.py >> /tmp/bo.log
sleep 90
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys

