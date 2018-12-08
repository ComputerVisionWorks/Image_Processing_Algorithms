﻿import cv2 as cv
import numpy as np
np.set_printoptions(threshold=np.inf)
import math
import copy

#   @class                              二值区域信息
#   @member label                       区域的标记
#   @member size                        区域像素个数
#   @member topLeft                     区域外接矩形左上点
#   @member bottomRigh                  区域外接矩形右下点
class BwArea:
    def __init__(self,_label = -1,_size = 0):
        self.label = _label
        self.size = _size
        self.topLeft = [99999999,99999999]
        self.bottomRight = [-1,-1]

#   @fn                                 更新区域外接矩形两个角点
#   @param  _x                          输入x坐标
#   @param  _y                          输入y坐标
#   @return                             返回自己
    def updatePos(self,_x,_y):
        self.topLeft[0] = min(self.topLeft[0],_x)
        self.topLeft[1] = min(self.topLeft[1],_y)
        self.bottomRight[0] = max(self.bottomRight[0],_x)
        self.bottomRight[1] = max(self.bottomRight[1],_y)
        return self
#   @class                              标记
#   @member parent                      标记的parent
#   @member root                        标记的root
class Label:
    def __init__(self, _parent = -1, _root = -1):
        self.parent = _parent
        self.root = _root

#   @notice                             list index（list中下标） == parent == root的label为某集合的root
#   @class                              标记并查集
#   @member label                       存放class Label的list()
#   @member __size                      并查集大小
#   @member helperCnt                   路径压缩helper函数调用计数器
class LabelUnionFind:

    def __init__(self):
        self.label = list()
        self.__size = 0
        self.helperCnt = 0

    #   @fn                             在list末尾添加新Label
    #   @param  _parent                 新Label.parent
    #   @param  _root                   新Label.root
    #   @return                         void
    def addLabel(self, _parent, _root):
        if(_parent < 0 or _root < 0 or _parent > self.__size or _root > self.__size):
            print("Error: Invalid parent or root!")
            raise
        self.label.append(Label(_parent, _root))
        self.__size += 1

    #   @fn                             在list末尾添加新Root Label
    #   @return                         void
    def addRootLabel(self):
        self.label.append(Label(self.__size, self.__size))
        self.__size += 1

    #   @fn                             路径压缩，即更新每个Label.root
    #   @return                         void
    def pathCompression(self):
        for i in range(self.__size - 1, -1, -1):
            self.label[i].root = self.__pathCompressionHelper1(self.label[i].root)

    #   @notice                         两种helper好像调用次数一样，helper1栈占用小一些
    #   @fn                             路径压缩helper1，方法为沿着Label.root递归
    #   @param  _root                   当前的Label.root
    #   @return                         集合的root
    def __pathCompressionHelper1(self, _root):
        self.helperCnt += 1
        # 若index的root等于index，则该index代表的Label为root label
        if(self.label[_root].root == _root):
            return _root
        # 否则沿着Label.root向上进行递归
        self.label[_root].root = self.__pathCompressionHelper1(self.label[_root].root)
        return self.label[_root].root

    #   @fn                             路径压缩helper2，方法为沿着Label.parent递归
    #   @param  _root                   当前的Label.root
    #   @param  _parent                 当前的Label.parent
    #   @renturn                        集合的root
    def __pathCompressionHelper2(self, _root, _parent):
        self.helperCnt += 1
        # 若index的root等于index，则该index代表的Label为root label
        if(self.label[_root].root == _root):
            return _root
        # 否则沿着Label.parent向上进行递归
        self.label[_parent].root = self.__pathCompressionHelper2(self.label[_parent].root, self.label[_parent].parent)
        return self.label[_parent].root

    #   @fn                             合并两个Label，并更新Label1到Label1.root路径下所有的label.root
    #   @param  _label1                 Label1
    #   @param  _label2                 Label2
    #   @return                         void
    def uinonLabel(self, _label1, _label2):
        if(_label1 < 0 or _label2 < 0 or _label1 > self.__size or _label2 > self.__size):
            print("Error: Invalid label or new parent!")
            raise
        # root相更新Label1.parent
        if(self.label[_label1].root == self.label[_label2].root):
            self.label[_label1].parent = _label2
        # root不相等循环更改Label1到Label1.root路径下所有Label.root
        else:
            newRoot = self.label[_label2].root
            tmpLabel = _label1
            while(self.label[tmpLabel].parent != tmpLabel):
                self.label[tmpLabel].root = newRoot
                tmpLabel = self.label[tmpLabel].parent
            # 更新Label1.root.root，Label1.root.parent
            self.label[tmpLabel].parent = newRoot
            self.label[tmpLabel].root = newRoot
            # 最后更新Label1.parent
            self.label[_label1].parent = _label2


#   @fn                                 two-pass法标记联通区域
#   @param  src                         输入二值图像(0 - 255)
#   @return                             连通区域信息
def twoPass(src):
    # 扩充上限以标记更多连通区域
    dst = np.zeros(src.shape,dtype = 'uint16')
    rows = src.shape[0]
    cols = src.shape[1]
    MAX_PIXEL_VAL = 255
    # two-pass
    label = np.uint16(1)
    # union-find，下标为label，uf[label]为映射的parent label
    uf = list([np.uint16(0)])
    for i in range(0,rows):
        for j in range(0,cols):
            # 该点为目标时
            if(src[i][j] == MAX_PIXEL_VAL):
                top = 0
                left = 0
                if(i-1 >= 0):
                    top = dst[i-1][j]
                if(j-1 >= 0):
                    left = dst[i][j-1]
                # 左和上都为无效像素值，赋新label并加入union-find中
                if(top == 0 and left == 0):
                    dst[i][j] = label
                    uf.append(label)
                    label += 1
                # 左和上都为label时
                elif(top > 0 and left > 0):
                    # 如果label相等，则该点赋左或上的值
                    if(top == left):
                        dst[i][j] = top
                    # 如果label不相等，则该点赋两点最小的label，并更新union-find
                    else:
                        minVal = min(top,left)
                        maxVal = max(top,left)
                        dst[i][j] = np.uint16(minVal)
                        uf[maxVal] = np.uint16(minVal)
                # 如果左和上只有一个点有效，则该点赋有效点的label
                elif(top > 0 or left > 0):
                    dst[i][j] = max(top,left)

    # 更新union-find，使每一个label映射到相应的集合里，同时维护一个uniqueLabel
    uniqueLabel = list()
    for i in range(1,len(uf)):
        if(uf[i] == i):
            uniqueLabel.append(uf[i])
            continue
        mark = uf[i]
        # 如果某label映射自己，则该label为root label，否则循环找该label映射parent label并直到找到root label
        while(uf[mark] != mark):
            mark = uf[mark]
        uf[i] = mark

    # 创建一个dict，将uniqueLabel映射到以1为起始
    mappedLabel = dict()
    for i in range(0,len(uniqueLabel)):
        mappedLabel[uniqueLabel[i]] = i+1
    # 映射
    for i in range(1,len(uf)):
        uf[i] = mappedLabel[uf[i]]

    # 建立area list
    areas = list()
    for i in range(0,len(mappedLabel)+1):
        areas.append(BwArea(i))

    # 使单个连通区域内的label一致化，同时更新areas list信息
    for i in range(0,rows):
        for j in range(0,cols):
            if(dst[i][j] > 0):
                dst[i][j] = uf[dst[i][j]]
                areas[dst[i][j]].size += 1
                areas[dst[i][j]] = areas[dst[i][j]].updatePos(i,j)

    # 连通区域标记不同颜色
    labeledImg = copy.deepcopy(src)
    labeledImg = cv.cvtColor(labeledImg,cv.COLOR_GRAY2BGR)
    for i in range(0,rows):
        for j in range(0,cols):
            labeledImg[i][j] = [(dst[i][j]*121)%255,(dst[i][j]*246)%255,(dst[i][j]*336)%255]
    # 连通区域标记
    for i in range(1,len(areas)):
        cv.putText(labeledImg,str(areas[i].label),
                   (areas[i].bottomRight[1],areas[i].bottomRight[0]),
                   cv.FONT_HERSHEY_SIMPLEX,1,(255,255,255),1)
    cv.imshow("labeledImg",labeledImg)
    return areas

input = cv.imread("F://MBR.bmp",cv.IMREAD_GRAYSCALE)
input = cv.threshold(input,20,255,cv.THRESH_BINARY)
input = input[1]
areas = twoPass(input)
cv.imshow("input",input)
cv.waitKey(0)