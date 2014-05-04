#!/bin/bash

sudo apt-get -y update
sudo apt-get -y upgrade

#Support programs

echo "Getting favorite programs"
sudo apt-get install -y emacs24
sudo apt-get install -y texlive
sudo apt-get install -y guake
sudo apt-get install -y git
sudo apt-get install -y synaptic

echo "Browsers and multimedia"
sudo apt-get install -y chromium-browser
sudo apt-get install -y flashplugin-nonfree
sudo apt-get install -y libmono-wcf3.0a-cil
sudo apt-get install -y vlc

echo "Camera stuff"
sudo apt-get install -y v4l-utils
sudo apt-get install -y v4l-conf
sudo apt-get install -y guvcview
sudo apt-get install -y cheese





# Setup Git & project
echo "Setting up Git"
git config --global user.name "Valerie Simonis"
git config --global user.email valerie.simonis@gmail.com
git config --global color.ui true

mkdir worm
cd worm
git init
git remote add w2 https://github.com/vsimonis/worm2.git
git pull w2 master
echo "Git ready to use"

# Python libraries
sudo apt-get install -y python-skimage
sudo apt-get install -y python-sklearn
sudo apt-get install -y python-pandas



echo "To-Do"
echo "1. add auctex to emacs"
echo "2. setup .emacs for fullscreen"

#chmod +x setup-machine.sh

