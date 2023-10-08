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


# reserviorList = []
# reserviorList.extend(reservior)


def VrateCheck(VrateList, predictRate):  # 根据计算出的predictRate，在VrateList中选择合适的速率
    Vrate = 0
    if predictRate >= max(VrateList):
        Vrate = max(VrateList)
    elif predictRate <= min(VrateList):
        Vrate = min(VrateList)
    elif max(VrateList) > predictRate > min(VrateList):
        for i in range(1, len(VrateList)):
            if VrateList[i - 1] <= predictRate < VrateList[i]:
                Vrate = VrateList[i - 1]
                break
    return int(max(Vrate, min(VrateList)))


def simulatePlay(BandWidth):
    # VrateList = [200, 400, 800, 1200, 2200, 3300, 5000, 6500, 8600]  # kbps
    VrateList = [235, 375, 560, 750, 1050, 1750, 2350, 3000, 5000]  # kbps

    # 初始变量
    avgRate = 0
    startupSegNum = 2 # 确保在buffer里边有两秒的视频才能开始播放
    N = 0
    Nmax = 0
    VrateTmp = VrateList[N]  # 初始比特率
    segmentDuration = 4 # 每个块播放4秒
    reservior = 90  # 蓄水池初始大小被设为90s
    # 跟随状态变量
    playback = []  # playback 是记录每一个0.1s的播放状态，0的话表示正在卡顿，1表示不卡顿
    playTime = 0  # 播放时间
    downloadDuration = 0  # 已经下载的segment的总时间
    buffLevel = 0  # 当前buffer水平
    bytesLeft = 0
    startSegmentDownloadTime = 0  # 该段开始下载的时间
    endSegmentDownloadTime = 0  # 该段结束下载的时间
    segmentDownloadRateList = []  # 该段下载的平均速率
    segNum = 0
    toRecv = min(segmentDuration,
                 videoDuration - downloadDuration)  # 下一个要接受的segement的长度，虽然segement长度固定，但在视频尾部可能会小于正常的segement长度

    bufferFifo = []  # 存放当前存在于buffer的数据
    startupDuration = 0
    rebufferDuration = 0
    deltaB = 0
    deltaB_factor = 0.875
    finishFlag = 0
    rebufFlag = 0

    # 算法特有变量
    bufferCapacity = 240  # 缓冲区大小240秒
    threshHold = 8
    buffLstTime = 0
    startupPhaseFlag = 0  # 判断是否处于startup阶段
    Nstartup = 0

    # 测试变量
    throughputList = []
    inputBitrate = []
    bufferTimeList = []

    indexList = range(0, len(BandWidth))
    for currentTime in indexList:

        currentBW = BandWidth[currentTime] * 8  # 当前网络带宽，乘8将KBps换算成kbps

        if buffLevel < (bufferCapacity - segmentDuration):  # 缓冲区中还能装下一个新段
            bytesLeft = bytesLeft + currentBW
            # print("bytesLeft", bytesLeft)

        else:  # 装不下了，当前不进行下载 该段的开始下载时间就向后推迟1秒
            # bytesLeft = 0
            startSegmentDownloadTime = currentTime + 1

        inputBitrate.extend([VrateTmp])
        bufferTimeList.extend([buffLevel])
        throughputList.extend([currentBW])

        # 下载
        if bytesLeft >= VrateTmp * toRecv:  # 判断当前网络带宽能否以选择的速率下载完一块

            bytesLeft = 0  # 当前带宽清零
            buffLevel = buffLevel + toRecv  # 缓冲区填充
            SelectedRateList.extend([VrateTmp])  # 记录当前速率
            downloadDuration = downloadDuration + toRecv  # 记录当前已经下载了多少块
            segNum += 1  # 块号加1

            for i in range(toRecv):
                bufferFifo.extend([VrateTmp])  # 记录每一秒的下载速率

            endSegmentDownloadTime = currentTime + 1
            # 记录某一段视频的下载速率，（视频大小/视频下载时间）保留四位小数
            segmentDownloadRateList.extend(
                [round(float(segmentDuration * VrateTmp) / (endSegmentDownloadTime - startSegmentDownloadTime), 4)])

            toRecv = min(segmentDuration, videoDuration - downloadDuration)  # 下一个要接受的segement片段长度

            if downloadDuration == videoDuration:  # 全部segment下载完
                break

            # 动态计算蓄水池大小
            # deltareservior = int(currentBW - VrateTmp) * 480 / 235
            # reservior = reservior + deltareservior
            # if reservior < 8:
            #     reservior = 8
            # elif reservior > 140:
            #     reservior = 140
            # reserviorList.extend(reservior)
            # print("蓄水池", reservior)
            deltaB = segmentDuration - (VrateTmp * segmentDuration) / currentBW
            # 确定下一个seg的比特率
            if segNum >= startupSegNum:

                # BBA2

                if buffLevel < reservior:  # buffer容量在lower reservior中

                    if deltaB > deltaB_factor * segmentDuration:
                        N = N + 1
                        Nmax = max(Nmax, N)

                elif reservior <= buffLevel:  # 在斜线中找到buffer的容量所对应的比特率

                    scalarVal = (float(max(VrateList) - min(VrateList))) / float(bufferCapacity - reservior)  # 斜率
                    proposedRate = (scalarVal * (buffLevel - reservior)) + VrateList[Nmax]
                    quantizedRate = VrateCheck(VrateList, proposedRate)
                    avgRate = numpy.mean(SelectedRateList)
                    print("平均速率", avgRate)
                    quantizedRate2 = VrateCheck(VrateList, avgRate)
                    N = max(VrateList.index(quantizedRate), VrateList.index(quantizedRate2))

                VrateTmp = VrateList[N]

        # 播放
        if segNum < startupSegNum:  # 处在初始缓冲中，要保证buffer里面有2s的缓存才能播放

            playback.extend([0])
            startupDuration = startupDuration + 1  # 开始播放时间推迟1秒


        else:  # 初始缓冲已经结束

            if buffLevel >= 1:  #
                playback.extend([1])
                playTime = playTime + 1
                buffLevel = buffLevel - 1
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
SelectedRateList = []  # 记录每一个segment的比特率
count = 0
TBandWidth = []
fr = open("./NewFile-HighDensity-CUHK.txt", 'r')
# fr = open("./lowDensity.txt", 'r')
for line in fr:
    TBandWidth.extend([int(line.split("\n")[0])])
    count += 1
    if (count > BWend):
        break
fr.close()
print("总时长", count)
videoDuration = 1000

ratio = 1.0

playback, bufferTimeList, throughputList, inputBitrate = simulatePlay(TBandWidth[BWstart:BWend])

throughputList = [float(num) / 1024 for num in throughputList]
inputBitrate = [float(num) / 1024 for num in inputBitrate]

startPoint = 0
endPoint = len(playback)
print("总播放时长", endPoint)
x = range(startPoint, endPoint)
# plt.scatter(x, playback[startPoint:endPoint], label='rebuffer')
# plt.plot(x, bufferTimeList[startPoint:endPoint], label='buffer time')
# plt.plot(x, throughputList[startPoint:endPoint], label='throughput')
# plt.plot(x, inputBitrate[startPoint:endPoint], label='request bitrate')
#
avg = numpy.mean(SelectedRateList)
print("平均速率", avg)
switchcnt = 0
temprate = SelectedRateList[0]
for rate in SelectedRateList:
    if rate != temprate:
        switchcnt += 1
        temprate = rate

print("切换频率", switchcnt)
endPoint = len(SelectedRateList)
x = range(startPoint, endPoint)
plt.plot(x, SelectedRateList[startPoint:endPoint], label='selected bit rate', c='blue', marker='^')
# plt.scatter(x, SelectedRateList[startPoint:endPoint], s=50, c='orange', marker='^')
VrateList = [235, 375, 560, 750, 1050, 1750, 2350, 3000, 5000]
[plt.axhline(ele , linestyle='--', color='gray') for ele in VrateList]
plt.xlabel('time/1 second')
plt.ylabel('playback')
plt.legend(loc='upper left', fontsize='xx-large')
plt.tight_layout()
plt.show()
num = str(playback).count("0")
print("卡顿次数", num)
