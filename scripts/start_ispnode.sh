case $(hostname) in
    node15.washington.vicci.org) CONFIG=ISP1_EG.json ;;
    node16.washington.vicci.org) CONFIG=ISP1_EG.json ;;
    node17.washington.vicci.org) CONFIG=ISP1_EG.json ;;

    node28.washington.vicci.org) CONFIG=ISP2_ING.json ;;
    node30.washington.vicci.org) CONFIG=ISP2_ING.json ;;
    node37.washington.vicci.org) CONFIG=ISP2_ING.json ;;
    node36.princeton.vicci.org) CONFIG=ISP2_ING.json ;;
    node37.princeton.vicci.org) CONFIG=ISP2_ING.json ;;
    node38.princeton.vicci.org) CONFIG=ISP2_ING.json ;;

    node15.stanford.vicci.org) CONFIG=ISP2_EG.json ;;
    node16.stanford.vicci.org) CONFIG=ISP2_EG.json ;;
    node17.stanford.vicci.org) CONFIG=ISP2_EG.json ;;

    node26.stanford.vicci.org) CONFIG=ISP3_ING.json ;;
    node22.stanford.vicci.org) CONFIG=ISP3_ING.json ;;
    node23.stanford.vicci.org) CONFIG=ISP3_ING.json ;;

    *) exit ;;
esac

#IP=$(ifconfig | grep 10.128 | awk '{print $2}' | cut -c 6-)

# use external ip
IP=$(ping $HOSTNAME -c 1 | head -1 | awk '{print $3}' | tr -d '()')

cd /taas
git pull
/taas/src/stack/serval -s -a $IP -d -i eth0

cd /reliable-isp
git pull
nohup python daemons/watcherd.py $CONFIG $IP > foo.out 2> foo.err < /dev/null &
nohup python daemons/failoverd.py $CONFIG > /reliable-isp/failover.out 2> /reliable-isp/failover.err < /dev/null &
echo "started"
