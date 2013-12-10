for i in {1001..1100}
do
    echo "creating client for $i"
    service_id=$(python /reliable-isp/clients/circuitc.py 10.128.114.14 10.128.114.22 10.128.114.26 10.128.114.31 $i 2> /dev/null|grep "0, taas=" | awk '{print $6}' | cut -c 6-)
    /reliable-isp/clients/udp_taas_client 10.128.114.11 `expr $i + 1000` $service_id 10.128.114.15 5 > /tmp/clients/$i.log &
done
