case $(hostname) in
    node12.washington.vicci.org) echo $hostname ;;
    node25.washington.vicci.org) echo $hostname ;;
	node25.stanford.vicci.org) echo $hostname ;;
	node18.stanford.vicci.org) echo $hostname ;;

    *) exit ;;
esac

# use external ip
#IP=$(ping $HOSTNAME -c 1 | head -1 | awk '{print $3}' | tr -d '()')

/zookeeper-3.4.5/bin/zkServer.sh start
