# -*- coding: UTF-8 -*-
import random
import string
import matplotlib
import numpy
import scipy
import pyparsing
import math
import matplotlib.pyplot as plt
from matplotlib import pylab


def VrateCheck(VrateList, predictRate):  # 根据计算出的predictRate，在VrateList中选择合适的速率
    Vrate = 0
    if predictRate >= max(VrateList):
        Vrate = max(VrateList)
    elif predictRate <= min(VrateList):
        Vrate = min(VrateList)
    elif predictRate < max(VrateList) and predictRate > min(VrateList):
        for i in range(1, len(VrateList)):
            if predictRate >= VrateList[i - 1] and predictRate < VrateList[i]:
                Vrate = VrateList[i - 1]
                break
    return int(max(Vrate, min(VrateList)))


def simulatePlay(BWSeries):
    VrateList = [200, 400, 800, 1200, 2200, 3300, 5000, 6500, 8600]  # kbps

    # 初始变量
    startupSegNum = 2  # seg
    N = 0
    VrateTmp = VrateList[N]  # 初始比特率
    segmentDuration = 4

    # 跟随状态变量
    playback = []  # playback 是记录每一个0.1s的播放状态，0的话表示正在卡顿，1表示不卡顿
    playTime = 0  # 播放时间
    downloadDuration = 0  # 已经下载的segment的总时间
    buffTime = 0
    bytesLeft = 0
    startSegmentDownloadTime = 0
    endSegmentDownloadTime = 0
    segmentDownloadRateList = []
    segNum = 0
    toRecv = min(segmentDuration,
                 videoDuration - downloadDuration)  # 下一个要接受的segement的长度，虽然segement长度固定，但在视频尾部可能会小于正常的segement长度
    SelectedRateList = []  # 记录每一个segment的比特率
    bufferFifo = []  # 存放当前存在于buffer的数据
    startupDuration = 0
    rebufferDuration = 0
    finishFlag = 0
    rebufFlag = 0

    # 算法特有变量
    reservior = 90  # second
    bufferCapacity = 240
    threshHold = 8
    buffLstTime = 0
    startupPhaseFlag = 0  # 判断是否处于startup阶段
    Nstartup = 0

    # 测试变量
    throughputList = []
    inputBitrate = []
    bufferTimeList = []

    indexList = range(0, len(BWSeries))
    for currentTime in indexList:

        currentBW = BWSeries[currentTime] * 8

        if (buffTime < (bufferCapacity - segmentDuration)):
            bytesLeft = bytesLeft + currentBW

        else:
            startSegmentDownloadTime = currentTime + 1

        inputBitrate.extend([VrateTmp])
        bufferTimeList.extend([buffTime])
        throughputList.extend([currentBW])

        # 下载
        if bytesLeft >= VrateTmp * toRecv:  # 当前接收到的数据是一个完整的segment

            bytesLeft = 0
            buffTime = buffTime + toRecv
            SelectedRateList.extend([VrateTmp])
            downloadDuration = downloadDuration + toRecv
            segNum += 1

            for i in range(toRecv):
                bufferFifo.extend([VrateTmp])

            endSegmentDownloadTime = currentTime + 1
            segmentDownloadRateList.extend(
                [round(float(segmentDuration * VrateTmp) / (endSegmentDownloadTime - startSegmentDownloadTime), 4)])

            toRecv = min(segmentDuration, videoDuration - downloadDuration)  # 下一个要接受的segement片段长度

            if downloadDuration == videoDuration:  # 全部segment下载完
                break

            # 确定下一个seg的比特率
            if segNum >= startupSegNum:

                # BBA0

                if buffTime < reservior:  # buffer容量在lower reservior中

                    N = 0    # reservior 还没装满，保持Rmin速率下载

                elif buffTime > int(bufferCapacity * 0.9):  # 装满了整个buffer的90%，buffer容量在upper reservior中，比特率调到最大
                    N = len(VrateList) - 1

                elif buffTime >= reservior and buffTime <= int(bufferCapacity * 0.9):  # 在斜线中找到buffer的容量所对应的比特率

                    scalarVal = (float(max(VrateList) - min(VrateList))) / float(bufferCapacity * 0.9 - reservior)  # 斜率
                    proposedRate = (scalarVal * (buffTime - reservior)) + min(VrateList)
                    quantizedRate = VrateCheck(VrateList, proposedRate)

                    N = VrateList.index(quantizedRate)

                VrateTmp = VrateList[N]

        # 播放
        if (segNum < startupSegNum):  # 处在初始缓冲中

            playback.extend([0])
            startupDuration = startupDuration + 1


        else:  # 初始缓冲已经结束

            if buffTime >= 1:
                playback.extend([1])
                playTime = playTime + 1
                buffTime = buffTime - 1
                bufferFifo.pop(0)

            else:
                playback.extend([0])
                rebufferDuration = rebufferDuration + 1
                rebufFlag = 1

    # 输出统计变量

    averageBitrate = float(sum(SelectedRateList)) / segNum
    qualityVar = sum(
        [math.fabs(SelectedRateList[i] - SelectedRateList[i - 1]) for i in range(1, len(SelectedRateList))])
    utility = averageBitrate - qualityVar / (segNum) - 6000 * float(
        rebufferDuration + startupDuration) / segNum  # 原始QOE

    print("QoE", utility)

    return playback, bufferTimeList, throughputList, inputBitrate


BWstart = 0
BWend = 2 * 1000

count = 0
TBWSeries = []
fr = open("./lowDensity.txt", 'r')
for line in fr:
    TBWSeries.extend([int(line.split("\n")[0])])
    count += 1
    if (count > BWend):
        break
fr.close()

videoDuration = 1000

ratio = 1.0

playback, bufferTimeList, throughputList, inputBitrate = simulatePlay(TBWSeries[BWstart:BWend])

throughputList = [float(num) / 1024 for num in throughputList]
inputBitrate = [float(num) / 1024 for num in inputBitrate]

startPoint = 0
endPoint = len(playback)

x = range(startPoint, endPoint)
plt.plot(x, playback[startPoint:endPoint], label='rebuffer')
# plt.plot(x, bufferTimeList[startPoint:endPoint], label='buffer time')
# plt.plot(x, throughputList[startPoint:endPoint], label='throughput')
# plt.plot(x, inputBitrate[startPoint:endPoint], label='request bitrate')


plt.xlabel('time/1 second')
plt.ylabel('y')
plt.legend(loc='upper center')
plt.show()
