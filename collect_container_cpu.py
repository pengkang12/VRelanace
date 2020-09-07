#!/bin/python3
import requests
import sys
import time
import os

os.system("kubectl top pod > /tmp/kube-cpu.txt")
time.sleep(5)
for i in range(50):
    os.system("kubectl top pod >> /tmp/kube-cpu.txt")
    time.sleep(1)
