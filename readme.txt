如果HCNetSDKCom目录以及libhcnetsdk.so、libhpr.so、libHCCore文件和可执行文件在同一级目录下，则使用同级目录下的库文件;
如果不在同一级目录下，则需要将以上文件的目录加载到动态库搜索路径中，设置的方式有以下几种:
一.	将网络SDK各动态库路径加入到LD_LIBRARY_PATH环境变量
	1.在终端输入：export  LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/XXX:/XXX/HCNetSDKCom      只在当前终端起作用
	2. 修改~/.bashrc或~/.bash_profile，最后一行添加 export  LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/XXX:/XXX/HCNetSDKCom，保存之后，使用source  .bashrc执行该文件 ，当前用户生效
	3. 修改/etc/profile，添加内容如第2条，同样保存之后使用source执行该文件  所有用户生效

二．在/etc/ld.so.conf文件结尾添加网络sdk库的路径，如/XXX和/XXX/HCNetSDKCom/，保存之后，然后执行ldconfig 

三．可以将网络sdk各依赖库放入到/lib64或usr/lib64下

四．可以在Makefile中使用-Wl,-rpath来指定动态路径，但是需要将网络sdk各个动态库都用 –l方式显示加载进来
	比如：-Wl,-rpath=/XXX:/XXX/HCNetSDKCom -lhcnetsdk  -lhpr –lHCCore –lHCCoreDevCfg –lStreamTransClient –lSystemTransform –lHCPreview –lHCAlarm –lHCGeneralCfgMgr –lHCIndustry –lHCPlayBack –lHCVoiceTalk –lanalyzedata -lHCDisplay


推荐使用一或二的方式，但要注意优先使用的是同级目录下的库文件。


2、具体的命令格式如下：

海康NVR视频管理工具使用说明：

列出NVR上的ip摄像头信息：
hik [NVRIP] [port] [userName] [password] list
按时间和通道号下载视频
hik [NVRIP] [port] [userName] [password] download [startTime] [endTime] [channel] [dir]
按照视频文件名下载视频
hik [NVRIP] [port] [userName] [password] download [srcFile] [desFile]
按时间和端口号查看视频文件块
hik [NVRIP] [port] [userName] [password] queryBlock [startTime] [endTime] [channel]

example:
hik 10.103.241.224 8000 admin 632911632 download 20150413101055 20150414105055 37 d:/file
D:/hiktool/hik 10.103.242.225 8000 admin 632911632 list
hik 10.103.242.225 8000 admin 632911632 queryBlock 20150413101055 20150414105055 31 d:/file

hik 10.103.242.225 8000 admin 632911632 download 20151228101055 20151228121055 33 /home/
