kill `ps -ef | grep serval | grep -v grep | awk '{print $2}'` || true
kill `ps -ef | grep watcherd | grep -v grep | awk '{print $2}'` || true
kill `ps -ef | grep failoverd | grep -v grep | awk '{print $2}'` || true
kill `ps -ef | grep circuitd | grep -v grep | awk '{print $2}'` || true
