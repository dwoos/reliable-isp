case $(hostname) in
    node12.washington.vicci.org) echo $hostname ;;
    node25.washington.vicci.org) echo $hostname ;;
    node35.washington.vicci.org) echo $hostname ;;
	node25.stanford.vicci.org) echo $hostname ;;
	node18.stanford.vicci.org) echo $hostname ;;

    *) exit ;;
esac

IP=$(ping $HOSTNAME -c 1 | head -1 | awk '{print $3}' | tr -d '()')

echo $IP

/zookeeper-3.4.5/bin/zkCli.sh -server $IP rmr /circuit

kill $(cat /tmp/zookeeper/zookeeper_server.pid )

echo "zk nodes cleared"


