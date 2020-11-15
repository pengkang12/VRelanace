rm /tmp/bo.log 
rm /tmp/bo_*
rm /tmp/kube-cpu.txt 
rm /tmp/skopt_input*
rm /tmp/skopt_model*


#echo "0, 10" > /tmp/window_ETLTopologySys.txt
#echo "0, 10" > /tmp/window_IoTPredictionTopologySYS.txt


bash script/redis-data.sh

python collect_container_cpu.py &
sleep 120
for i in {1..721}
do
python collect_container_cpu.py &
python ui.py ETLTopologySys &
python ui.py IoTPredictionTopologySYS &
python ui.py IoTPredictionTopologyTAXI &
python ui.py ETLTopologyTaxi &

sleep 45
python BO/bayesian_optimization.py >> /tmp/bo.log
sleep 75
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologyTAXI

