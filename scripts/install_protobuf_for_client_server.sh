cd /
wget https://protobuf.googlecode.com/files/protobuf-2.5.0.tar.bz2
bunzip2 protobuf-2.5.0.tar.bz2
tar -xvf protobuf-2.5.0.tar
cd /protobuf-2.5.0
./configure --prefix=/usr


make
make install

cd /
wget https://protobuf-c.googlecode.com/files/protobuf-c-0.15.tar.gz .
tar -xzvf protobuf-c-0.15.tar.gz

echo "/usr/local/lib" >> /etc/ld.so.conf
sudo ldconfig

cd /protobuf-c-0.15
./configure && make && make install
