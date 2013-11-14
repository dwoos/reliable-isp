group :isps do
  host "isp1-a"
  host "isp1-b"
  host "isp2-a"
  host "isp2-b"

  each_host do
    role :circuitd
    role :failoverd
    role :forwarderd
  end
end

role :circuitd do
  task :start do
    cd "/vagrant/daemons"
    exec! "sh -c \"nohup python -u circuitd.py /vagrant/#{name.partition('-')[0]}.json > /tmp/circuitd.log 2>&1 &\""
  end

  task :stop do
    exec! "sh -c \"kill `ps -ef | grep circuitd | grep -v grep | awk '{print $2}'`\" || true"
  end

  task :restart do
    circuitd.stop
    circuitd.start
  end

  task :tail do
    tail '-F', '/tmp/circuitd.log', echo: true
  end
end

role :failoverd do
  task :start do
    cd "/vagrant/daemons"
    exec! "sh -c \"nohup python -u failoverd.py /vagrant/#{name.partition('-')[0]}.json > /tmp/failoverd.log 2>&1 &\""
  end

  task :stop do
    exec! "sh -c \"kill `ps -ef | grep failoverd | grep -v grep | awk '{print $2}'`\" || true"
  end

  task :restart do
    failoverd.stop
    failoverd.start
  end

  task :tail do
    tail '-F', '/tmp/failoverd.log', echo: true
  end
end

role :forwarderd do
  task :start do
    cd "/vagrant/daemons"
    exec! "sh -c \"nohup python -u forwarderd.py /vagrant/#{name.partition('-')[0]}.json > /tmp/forwarderd.log 2>&1 &\""
  end

  task :stop do
    exec! "sh -c \"kill `ps -ef | grep forwarderd | grep -v grep | awk '{print $2}'`\" || true"
  end

  task :restart do
    forwarderd.stop
    forwarderd.start
  end

  task :tail do
    tail '-F', '/tmp/failoverd.log', echo: true
  end
end
