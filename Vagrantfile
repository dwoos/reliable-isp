# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # global config
  config.vm.box = "raring64"

  config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/raring/current/raring-server-cloudimg-amd64-vagrant-disk1.box"

  # config for each box
  config.vm.define "client", primary: true do |box|
    box.vm.network "private_network", ip: "192.168.42.2"
    box.vm.provision "shell", path: "python-deps.sh"
  end

  config.vm.define "server" do |box|
    box.vm.network "private_network", ip: "192.168.42.3"
    box.vm.provision "shell", path: "python-deps.sh"
  end

  config.vm.define "isp1-a" do |box|
    box.vm.network "private_network", ip: "192.168.42.4"
    box.vm.provision "shell", path: "python-deps.sh"
  end

  config.vm.define "isp1-b" do |box|
    box.vm.network "private_network", ip: "192.168.42.5"
    box.vm.provision "shell", path: "python-deps.sh"
  end

  config.vm.define "isp2-a" do |box|
    box.vm.network "private_network", ip: "192.168.42.6"
    box.vm.provision "shell", path: "python-deps.sh"
  end

  config.vm.define "isp2-b" do |box|
    box.vm.network "private_network", ip: "192.168.42.7"
    box.vm.provision "shell", path: "python-deps.sh"
  end

  config.vm.define "isp1-zk" do |box|
    box.vm.network "private_network", ip: "192.168.42.8"
    box.vm.provision "shell", path: "zookeeper.sh"
  end

  config.vm.define "isp2-zk" do |box|
    box.vm.network "private_network", ip: "192.168.42.9"
    box.vm.provision "shell", path: "zookeeper.sh"
  end
end
