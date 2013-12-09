cd /

ifup eth0
ifup eth1
yum install -y git make automake gcc libtool gcc-c++ python-setuptools protobuf-python

git clone https://github.com/UWNetworksLab/taas.git
cd /taas/
./autogen.sh && ./configure --disable-java-bindings --disable-kernel && make

cd /
git clone https://github.com/dwoos/reliable-isp.git

git clone https://github.com/python-zk/kazoo.git
cd /kazoo
python setup.py install
