for i in {1001..1020}
do
    python /reliable-isp/clients/circuitc.py 10.128.114.14 10.128.114.22 10.128.114.26 10.128.114.31 $i 2> /dev/null|grep "0, taas=" | awk '{print $6}' | cut -c 6-
done
