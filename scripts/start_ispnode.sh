case $(hostname) in
    node15.washington.vicci.org) CONFIG=isp1.json ;;
    node17.washington.vicci.org) CONFIG=isp1.json ;;

    node18.washington.vicci.org) CONFIG=isp2.json ;;
    node23.washington.vicci.org) CONFIG=isp2.json ;;
    node24.washington.vicci.org) CONFIG=isp2.json ;;

    node27.washington.vicci.org) CONFIG=isp3.json ;;
    node28.washington.vicci.org) CONFIG=isp3.json ;;
    node30.washington.vicci.org) CONFIG=isp3.json ;;
    *) exit ;;
esac

IP=$(ifconfig | grep 10.128 | awk '{print $2}' | cut -c 6-)

cd /reliable-isp
git pull
/taas/src/stack/serval -s -a $IP -d -i eth0
nohup python daemons/watcherd.py $CONFIG $IP > foo.out 2> foo.err < /dev/null &
nohup python daemons/failoverd.py $CONFIG > /reliable-isp/failover.out 2> /reliable-isp/failover.err < /dev/null &
echo "started"
