case $(hostname) in
    *.washington.vicci.org) CONFIG=isp1.json ;;
    *.stanford.vicci.org ) CONFIG=isp2.json ;;
    *.princeton.vicci.org) CONFIG=isp3.json ;;
    *) exit ;;
esac

IP=$(curl -s http://ipecho.net/plain)

cd /reliable-isp
git pull
/taas/src/stack/serval -s -a $IP -d -i eth0
nohup python daemons/watcherd.py $CONFIG $IP > foo.out 2> foo.err < /dev/null &
nohup python daemons/failoverd.py $CONFIG > foo.out 2> foo.err < /dev/null &
echo "started"
