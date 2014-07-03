#!/usr/bin/env bash

YOUCOMPLETEME_DIR=$HOME/.spf13-vim-3/.vim/bundle/YouCompleteMe
INSTALL_DIR=$YOUCOMPLETEME_DIR/third_party/ycmd/ycmd/completers/

if [[ ! -d $YOUCOMPLETEME_DIR ]]
then
    echo "The path for youcompleteme isn't the good one!"
    echo "PATH: $YOUCOMPLETEME_DIR"
    exit 1
fi

if [[ ! -d $INSTALL_DIR ]]
then
    echo "The file structure of youcompleteme seems to be too old."
    echo "Upgrade it!"
    exit 1
fi

echo "Create directory into the youcompleteme configuration."
mkdir -p $INSTALL_DIR/tex

# get current directory
pushd . > /dev/null
current="${BASH_SOURCE[0]:-$0}";
while ([ -h "${current}" ]); do
    cd "`dirname "${current}"`"
    current="$(readlink "`basename "${current}"`")";
done
cd "`dirname "${current}"`" > /dev/null
current="`pwd`";
popd  > /dev/null

echo "Move files to it."
CP=$(which cp)
$CP -r $current/tex/*.py $INSTALL_DIR/tex/

echo "Installation done!"
