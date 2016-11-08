#!/bin/bash

TMP_FOLDER=tmp
BUILD_FOLDER=build

function get_image() {
    file=$1
    str=`readlink -f $file|awk -F'/' '{print \$NF}'`
    echo $str
}

# to extract options
BASE_IMAGE=$1
BUNDLE_VER=$2

if [[ "$BASE_IMAGE" == "" ]]; then
    echo "You need to assign the base image to build factory test image."
    exit 1
fi

if [ ! -f "$BASE_IMAGE" ]; then
    echo "The base image should be file. ex: chromiumos_factory_image.bin"
    exit 1
fi

if [[ "$BUNDLE_VER" == "" ]]; then
    echo "You need to assign bundle version to build factory test image."
    exit 1
fi

if [ ! -d "$TMP_FOLDER" ]; then
    echo "Creating the work folder \"$TMP_FOLDER\"..."
    mkdir $TMP_FOLDER
fi 

if [ ! -d "$BUILD_FOLDER" ]; then
    echo "Creating the output folder \"$BUILD_FOLDER\"..."
    mkdir $BUILD_FOLDER
fi

echo "Copying the base image $BASE_IMAGE to the work folder..."
cp $BASE_IMAGE $TMP_FOLDER

MOUNT_TOOL=$(readlink -f mount_partition)

TMP_IMAGE="$(get_image "$BASE_IMAGE")"

echo "Creating mount folder...."
STAT_P="$TMP_FOLDER/s"
ROOT_P="$TMP_FOLDER/m"

mkdir -p $STAT_P && mkdir -p $ROOT_P

echo "Mounting stateful partition as $STAT_P"
$MOUNT_TOOL -rw $TMP_FOLDER/$TMP_IMAGE 1 $STAT_P

echo "Mounting root partition as $ROOT_P"
$MOUNT_TOOL -rw $TMP_FOLDER/$TMP_IMAGE 3 $ROOT_P 

echo "Configuring upstart..."
sudo cp -a system/etc/init/* $ROOT_P/etc/init
sudo mv $ROOT_P/etc/init/factory.conf $ROOT_P/etc/init/factory.conf.disable
sudo mv $ROOT_P/etc/init/factorylog.conf $ROOT_P/etc/init/factorylog.conf.disable 

# compile factory scripts
cat>tmp/compile.py<<EOF
#!/usr/bin/env python
import compileall
import sys
import os
print "compile python scripts..."
compileall.compile_dir(sys.argv[1])
EOF

echo "Importing factory scripts..."
cp -a factory $TMP_FOLDER
python $TMP_FOLDER/compile.py $TMP_FOLDER/factory > /dev/null 2>&1

rm $TMP_FOLDER/factory/*.py
rm $TMP_FOLDER/factory/python/*.py
rm $TMP_FOLDER/factory/config/*.pyc 

sudo mkdir -p $STAT_P/dev_image/mfg

sudo cp -a $TMP_FOLDER/factory $STAT_P/dev_image/mfg
sudo mv $STAT_P/dev_image/mfg/factory $STAT_P/dev_image/mfg/ui

sudo mv $STAT_P/dev_image/mfg/ui/python $STAT_P/dev_image/mfg/ui/pydirs
sudo mv $STAT_P/dev_image/mfg/ui/shell $STAT_P/dev_image/mfg/ui/shdirs

sudo mkdir $STAT_P/dev_image/mfg/ui/grt
sudo mkdir $STAT_P/dev_image/mfg/ui/log

# link hardware component configure and gooftool
pushd . > /dev/null 2>&1
cd $STAT_P/dev_image/mfg/ui/grt
sudo ln -sf /usr/local/share/chromeos-hwid chromeos-hwid
sudo ln -sf /usr/local/gooftool gooftool
popd > /dev/null 2>&1

pushd . > /dev/null 2>&1
cd $ROOT_P/opt
sudo ln -sf /usr/local/mfg mfg
popd > /dev/null 2>&1

DATECODE=$(date +%Y%m%d.%H%M)
TAG_DESC=`git describe`
IMAGE_VERSION="${BUNDLE_VER}_${TAG_DESC}_${DATECODE}"
echo "$IMAGE_VERSION" > $STAT_P/dev_image/mfg/ui/version

echo "Unmounting stateful directory: $STAT_P"
sudo umount $STAT_P

echo "Unmounting root directory: $ROOT_P"
sudo umount $ROOT_P

BUILD_IMAGE="$BUILD_FOLDER/chromiumos_factory_test_zgb_m2_${IMAGE_VERSION}_image.bin.tbz2"

echo "Generating factory test image $BUILD_IMAGE"

pushd . > /dev/null 2>&1
cd tmp
if [[ $(type pv 2>/dev/null) ]]; then
    SIZE=`du -sk $TMP_IMAGE | cut -f 1`
    tar cvf - $TMP_IMAGE | pv -p -s ${SIZE}k | bzip2 -c > ../${BUILD_IMAGE}
else
    tar jcvf ../${BUILD_IMAGE} $TMP_IMAGE
fi
popd > /dev/null 2>&1

rm -rf $TMP_FOLDER

echo "Done."

exit

