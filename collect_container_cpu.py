#!/bin/python3
import requests
import sys
import time
import os

time.sleep(65)
os.system("kubectl top pod > /tmp/kube-cpu.txt")
for i in range(50):
    os.system("kubectl top pod >> /tmp/kube-cpu.txt")
    time.sleep(1)
