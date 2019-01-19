from PIL import Image
import numpy as np
import os


#分类器
class Classification():
    def __init__(self):
        pass

    def document(self):
        #目录
        FindPath = r'C:\Users\rely2\Pictures'
        FileNames = os.listdir(FindPath)
        #print(FileNames)
        for file_name in FileNames:
            if   file_name.endswith('jpg')\
              or file_name.endswith('png'):
                #文件名
                print(file_name)

            #fullfilename=os.path.join(FindPath,file_name)  



#下载器
class Download():
    def __init__(self):
        pass


 



Clf = Classification()
Clf.document()











