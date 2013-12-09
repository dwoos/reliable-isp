case $(hostname) in
    node14.washington.vicci.org) CONFIG=isp1.json ;;
    node22.washington.vicci.org ) CONFIG=isp2.json ;;
    node26.washington.vicci.org ) CONFIG=isp3.json ;;
    *) exit ;;
esac

cd /reliable-isp
git pull
nohup python daemons/circuitd.py $CONFIG > foo.out 2> foo.err < /dev/null &
echo "started"
