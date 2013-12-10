i=1
for circuit in `cat $1`
do
    n=`expr $i + 1000`
    echo "creating client for $n"
    /reliable-isp/clients/udp_taas_client 10.128.114.11 `expr $n + 1000` $circuit 10.128.114.15 5 &> /tmp/clients/$n.log &
    i=`expr $i + 1`
done
