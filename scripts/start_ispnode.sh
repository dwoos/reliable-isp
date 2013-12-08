case $(hostname) in
    *.washington.vicci.org) CONFIG=isp1.json ;;
    *.stanford.vicci.org ) CONFIG=isp2.json ;;
    *.princeton.vicci.org) CONFIG=isp3.json ;;
    *) exit ;;
esac

cd /reliable-isp
git pull
/taas/src/stack/serval -s -a $(curl -s http://ipecho.net/plain) -d
nohup python daemons/watcherd.py $CONFIG > foo.out 2> foo.err < /dev/null &
nohup python daemons/failoverd.py $CONFIG > foo.out 2> foo.err < /dev/null &
echo "started"
