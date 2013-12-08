case $(hostname) in
    *.washington.vicci.org) CONFIG=isp1.json ;;
    *.stanford.vicci.org ) CONFIG=isp2.json ;;
    *.princeton.vicci.org) CONFIG=isp3.json ;;
    *) exit ;;
esac

cd /reliable-isp
nohup python daemons/circuitd.py $CONFIG &
echo "started"
