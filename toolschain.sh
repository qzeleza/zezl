#!/bin/bash

ROOT_TOOLS=${1}

cd "${ROOT_TOOLS}" && cd .. || exit
rm -rf "${ROOT_TOOLS}"
apt update && apt upgrade -y

apt install -y build-essential ccache ecj fastjar file g++ gawk \
gettext git java-propose-classpath libelf-dev libncurses5-dev \
libncursesw5-dev libssl-dev python python2.7-dev python3 unzip wget \
python3-distutils python3-setuptools python3-dev rsync subversion \
swig time xsltproc zlib1g-dev autoconf automake bash bison bzip2 cvs diffutils file flex g++ \
gawk gettext git-core gperf groff-base libexpat1-dev libncurses-dev libssl-dev libtool \
libslang2 libxml-parser-perl make patch perl python ruby sed shtool subversion tar \
texinfo unzip zlib1g zlib1g-dev pkg-config gettext libgmp3-dev libmpfr-dev libmpc-dev \
gcc-multilib libtool-bin

# set en_US.UTF-8 locale
export LC_CTYPE=en_US.UTF-8
export LC_ALL=en_US.UTF-8
dpkg-reconfigure locales

git clone https://github.com/Entware/Entware.git && cd "${ROOT_TOOLS}" || exit
echo 'src-git keendev3x https://github.com/The-BB/keendev-3x.git' >> ./feeds.conf

cp "$(ls ${ROOT_TOOLS}/configs/mipsel-*)" .config
make package/symlinks