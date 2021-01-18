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
for i in {1..16}
do
python collect_container_cpu.py &
#python ui.py ETLTopologySys  &
#python ui.py IoTPredictionTopologySYS & 
#python ui.py IoTPredictionTopologyTAXI &
#python ui.py ETLTopologyTaxi &

nohup /usr/bin/time -f "%P %M" python ui.py ETLTopologySys  &
nohup /usr/bin/time -f "%P %M"  python ui.py IoTPredictionTopologySYS & 
nohup /usr/bin/time -f "%P %M" python ui.py IoTPredictionTopologyTAXI &
nohup /usr/bin/time -f "%P %M" python ui.py ETLTopologyTaxi &

sleep 45
#nohup /usr/bin/time -f "%P %M"  python BO/bayesian_optimization.py >> /tmp/bo.log & 
python BO/bayesian_optimization.py >> /tmp/bo.log &
sleep 75
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologyTaxi
kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys
kubectl exec nimbus -- /opt/apache-storm/bin/storm kill IoTPredictionTopologySYS
kubectl exec nimbus -- /opt/apache-storm/bin/storm kill IoTPredictionTopologyTAXI

