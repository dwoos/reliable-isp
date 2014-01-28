case $(hostname) in
    node14.washington.vicci.org) CONFIG=ISP1_EG.json ;;
    node26.washington.vicci.org ) CONFIG=ISP2_ING.json ;;
    node12.stanford.vicci.org ) CONFIG=ISP2_EG.json ;;
    node19.stanford.vicci.org ) CONFIG=ISP3_ING.json ;;
    *) exit ;;
esac

cd /reliable-isp
git pull
nohup python daemons/circuitd.py $CONFIG > foo.out 2> foo.err < /dev/null &
echo "started"
