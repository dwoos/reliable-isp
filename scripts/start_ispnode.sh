case $(hostname) in
    node15.washington.vicci.org) CONFIG=isp1.json ;;
    node16.washington.vicci.org) CONFIG=isp1.json ;;
    node17.washington.vicci.org) CONFIG=isp1.json ;;

    node27.washington.vicci.org) CONFIG=isp3.json ;;
    node28.washington.vicci.org) CONFIG=isp3.json ;;
    node30.washington.vicci.org) CONFIG=isp3.json ;;

    node37.washington.vicci.org) CONFIG=isp4.json ;;
    node38.washington.vicci.org) CONFIG=isp4.json ;;
    node39.washington.vicci.org) CONFIG=isp4.json ;;

    *) exit ;;
esac

IP=$(ifconfig | grep 10.128 | awk '{print $2}' | cut -c 6-)

cd /reliable-isp
git pull
/taas/src/stack/serval -s -a $IP -d -i eth0
nohup python daemons/watcherd.py $CONFIG $IP > foo.out 2> foo.err < /dev/null &
nohup python daemons/failoverd.py $CONFIG > /reliable-isp/failover.out 2> /reliable-isp/failover.err < /dev/null &
echo "started"
