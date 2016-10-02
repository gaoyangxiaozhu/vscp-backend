/*
 *
 *  Created on: Oct 29, 2014
 *  Author: zcan
 *
 *  Modified by Gyy on: Sep 8, 2016
 */
#include <iostream>
#include <cstdio>
#include <time.h>
#include <math.h>
#include <sys/stat.h>
#include "unistd.h"
#include "HCNetSDK.h"
#include "PlayM4.h"
#include "LinuxPlayM4.h"
#include <cstdlib>
#include<cstring>
#include<ctime>
#include<cerrno>
#include <fstream>

#define MAX_PATH 260

using namespace std;
HWND hWnd = 0;
/*
	nPort 当前获得的用于播放当前视频文件的通道号
 */
LONG nPort = -1;

/*
	destPath 要保存的路径+文件名 如 /home/gyy/data/test.jpg
 */
char destPath[100];
int state = 0;

time_t getTime(NET_DVR_TIME timeStru);
void getCmd(char * cmd,char *res);

LONG login(char *host, int port, char * user, char *password) {
	LONG iUserId = -1;
	NET_DVR_DEVICEINFO_V30 struDeviceInfo;
	NET_DVR_Init();
	NET_DVR_SetConnectTime(5000, 1);
	NET_DVR_SetReconnect(10000, true);
	iUserId = NET_DVR_Login_V30(host, port, user, password,&struDeviceInfo);
	if (iUserId < 0) {
		printf("Login error, %d\n", NET_DVR_GetLastError());
		NET_DVR_Cleanup();
		return -1;
	}
	printf("login success\n");
	return iUserId;
}


time_t getTime(NET_DVR_TIME timeStru){
	tm tmstr;
	tmstr.tm_year=timeStru.dwYear-1900;
	tmstr.tm_mon=timeStru.dwMonth-1;
	tmstr.tm_mday=timeStru.dwDay;
	tmstr.tm_hour=timeStru.dwHour;
	tmstr.tm_min=timeStru.dwMinute;
	tmstr.tm_sec=timeStru.dwSecond;
	tmstr.tm_isdst = 0;
	return mktime(&tmstr);
}

int getStatusByTime(LONG lUserID, char* start, char* end, int ipChannel, char* resCond){
	NET_DVR_FILECOND_V40 fileCond = { 0 };
	fileCond.dwFileType = 0xFF;
	fileCond.lChannel = ipChannel; //通道号
	fileCond.dwIsLocked = 0xFF;
	fileCond.dwUseCardNo = 0;
	//开始时间
	sscanf(start, "%4d%2d%2d%2d%2d%2d", &fileCond.struStartTime.dwYear,&fileCond.struStartTime.dwMonth,
			&fileCond.struStartTime.dwDay,&fileCond.struStartTime.dwHour,&fileCond.struStartTime.dwMinute,&fileCond.struStartTime.dwSecond);
	//结束时间
	sscanf(end, "%4d%2d%2d%2d%2d%2d",&fileCond.struStopTime.dwYear,&fileCond.struStopTime.dwMonth,&fileCond.struStopTime.dwDay,
			&fileCond.struStopTime.dwHour,&fileCond.struStopTime.dwMinute,&fileCond.struStopTime.dwSecond);

	long downloadStopTime = getTime(fileCond.struStopTime);
	long downloadStartTime = getTime(fileCond.struStartTime);

	if(downloadStopTime <= downloadStartTime){
		cout<<"the time is too short or wrong!!!"<<endl;
		return 0;
	}
	DWORD totalSize = 0;
	long cutTime = 0, endBlockStopTime = 0, blockStartTime = 0;
	int lFindHandle = NET_DVR_FindFile_V40(lUserID, &fileCond);
	if (lFindHandle < 0) {
		printf("find file fail,last error %d\n", NET_DVR_GetLastError());
		return 0;
	}
	NET_DVR_FINDDATA_V40 struFileData;
	int num = 0;
	while (true) {
		//逐个获取查找到的文件信息
		int result = NET_DVR_FindNextFile_V40(lFindHandle, &struFileData);
		if (result == NET_DVR_ISFINDING){
			continue;
		}//获取文件信息成功
		else if (result == NET_DVR_FILE_SUCCESS){
			num++;
			if(!totalSize){
				blockStartTime = getTime(struFileData.struStartTime);
				if(blockStartTime > downloadStartTime)
					downloadStartTime = blockStartTime;
			}else{
				cutTime += getTime(struFileData.struStartTime) - endBlockStopTime;
			}
			endBlockStopTime = getTime(struFileData.struStopTime);
			totalSize += struFileData.dwFileSize/1024;
		}
		else if (result == NET_DVR_FILE_NOFIND || result== NET_DVR_NOMOREFILE) //未查找到文件或者查找结束
		{
			break;
		}else {
			printf("find file fail for illegal get file state");
			break;
		}
	}
	//停止查找
	NET_DVR_FindClose_V30(lFindHandle);
	if(totalSize){
		if(endBlockStopTime < downloadStopTime)
			downloadStopTime = endBlockStopTime;
		long downloadTime = downloadStopTime - downloadStartTime;
		if(downloadTime <= 0) {
			return 0;
		}
		float perc = (float)(downloadTime - cutTime) / (endBlockStopTime - blockStartTime - cutTime); //可能出现endBlockStopTime > downloadStopTime 或者 blockStartTime < downloadStartTime

		sprintf(resCond, "%d:%ld:%d", num, downloadTime - cutTime, (int)(perc*totalSize));
	}else{
		return 0;
	}

	return 1;
}
int listCammera(LONG lUserID){
		UINT i=0;
		BYTE byIPID,byIPIDHigh;
		int iDevInfoIndex, iGroupNO;
		DWORD dwReturned = 0 ;
		//获取IP通道参数信息
		NET_DVR_IPPARACFG_V40 IPAccessCfgV40;
		iGroupNO=0;

	    if (!NET_DVR_GetDVRConfig(lUserID, NET_DVR_GET_IPPARACFG_V40, iGroupNO, &IPAccessCfgV40, sizeof(NET_DVR_IPPARACFG_V40), &dwReturned)){
	        printf("NET_DVR_GET_IPPARACFG_V40 error, %d\n", NET_DVR_GetLastError());
	        return 0;
	    }else{
	    	int start=IPAccessCfgV40.dwStartDChan;
	    	printf("start:%d\n", start);
	        for (i=0;i<IPAccessCfgV40.dwDChanNum;i++)
	        {
	            switch(IPAccessCfgV40.struStreamMode[i].byGetStreamType)
	            {
	            case 0: //直接从设备取流
                    byIPID=IPAccessCfgV40.struStreamMode[i].uGetStream.struChanInfo.byIPID;
                    byIPIDHigh=IPAccessCfgV40.struStreamMode[i].uGetStream.struChanInfo.byIPIDHigh;
                    iDevInfoIndex=byIPIDHigh*256 + byIPID-1-iGroupNO*64;
	                if (IPAccessCfgV40.struStreamMode[i].uGetStream.struChanInfo.byEnable)
	                    printf("channel:%d,IP:%s\n", i, IPAccessCfgV40.struIPDevInfo[iDevInfoIndex].struIP.sIpV4);
	                else if(strlen(IPAccessCfgV40.struIPDevInfo[iDevInfoIndex].struIP.sIpV4)>1)
	                    printf("unableChan:%d,IP:%s\n", i, IPAccessCfgV40.struIPDevInfo[iDevInfoIndex].struIP.sIpV4);
	                break;
	            case 1: //从流媒体取流
	                if (IPAccessCfgV40.struStreamMode[i].uGetStream.struPUStream.struStreamMediaSvrCfg.byValid){
	                    printf("IP channel %d connected with the IP device by stream server.\n", i);
	                    printf("IP of stream server: %s, IP of IP device: %s\n",IPAccessCfgV40.struStreamMode[i].uGetStream.\
	                    struPUStream.struStreamMediaSvrCfg.struDevIP.sIpV4, IPAccessCfgV40.struStreamMode[i].uGetStream.\
	                    struPUStream.struDevChanInfo.struIP.sIpV4);
	                }
	                break;
	            default:
	                break;
	            }
	        }
	    }
	    return 1;
}

int findFileBytimeAndIpChannle(LONG lUserID, const char* start, const char *end, int ipChannel) {
	NET_DVR_FILECOND_V40 struFileCond = { 0 };
	struFileCond.dwFileType = 0xFF;
	struFileCond.lChannel = ipChannel; //通道号
	struFileCond.dwIsLocked = 0xFF;
	struFileCond.dwUseCardNo = 0;
	printf("starting...\n");
	//开始时间
	sscanf(start, "%4d%2d%2d%2d%2d%2d", &struFileCond.struStartTime.dwYear,
			&struFileCond.struStartTime.dwMonth,
			&struFileCond.struStartTime.dwDay,
			&struFileCond.struStartTime.dwHour,
			&struFileCond.struStartTime.dwMinute,
			&struFileCond.struStartTime.dwSecond);
	//结束时间
	sscanf(end, "%4d%2d%2d%2d%2d%2d",
			&struFileCond.struStopTime.dwYear,
			&struFileCond.struStopTime.dwMonth,
			&struFileCond.struStopTime.dwDay,
			&struFileCond.struStopTime.dwHour,
			&struFileCond.struStopTime.dwMinute,
			&struFileCond.struStopTime.dwSecond);
	//查找录像文件
	int lFindHandle = NET_DVR_FindFile_V40(lUserID, &struFileCond);
	if (lFindHandle < 0) {
		printf("find file fail,last error %d\n", NET_DVR_GetLastError());
		return -1;
	}
	NET_DVR_FINDDATA_V40 struFileData;
	while (true) {
		//逐个获取查找到的文件信息
		int result = NET_DVR_FindNextFile_V40(lFindHandle, &struFileData);
		if (result == NET_DVR_ISFINDING) {
			continue;
		} else if (result == NET_DVR_FILE_SUCCESS) //获取文件信息成功
		{
			char startTime[20],endTime[20];
			sprintf(startTime,"%4d/%2d/%2d %2d:%2d:%2d",
					struFileData.struStartTime.dwYear,
					struFileData.struStartTime.dwMonth,
					struFileData.struStartTime.dwDay,
					struFileData.struStartTime.dwHour,
					struFileData.struStartTime.dwMinute,
					struFileData.struStartTime.dwSecond);
			sprintf(endTime,"%4d/%2d/%2d %2d:%2d:%2d",
					struFileData.struStopTime.dwYear,
					struFileData.struStopTime.dwMonth,
					struFileData.struStopTime.dwDay,
					struFileData.struStopTime.dwHour,
					struFileData.struStopTime.dwMinute,
					struFileData.struStopTime.dwSecond);
			printf("name:%s,start:%s,end:%s,size:%d\n",
					struFileData.sFileName,
					startTime,
					endTime,
					struFileData.dwFileSize);
		}
		else if (result == NET_DVR_FILE_NOFIND || result== NET_DVR_NOMOREFILE) //未查找到文件或者查找结束
		{
			break;
		} else {
			printf("find file fail for illegal get file state");
			break;
		}
	}

//	//停止查找
	if (lFindHandle >= 0) {
		NET_DVR_FindClose_V30(lFindHandle);
	}
	return 0;
}

/*
 * filename参数表示的是save后的文件路径
 */
int dowload(LONG userId, char* start, char* end, DWORD channel, char *fileName){
	char * blockStatus=(char *)malloc(sizeof(char)*30);
	if(!getStatusByTime(userId, start, end, channel, blockStatus))
		return 0;
	int num, totalDuration,filesize;
	sscanf(blockStatus,"%d:%d:%d",&num, &totalDuration, &filesize);
	free(blockStatus);
	NET_DVR_PLAYCOND struDownloadCond={0};
	struDownloadCond.dwChannel=channel;
	//开始时间
	sscanf(start, "%4d%2d%2d%2d%2d%2d", &struDownloadCond.struStartTime.dwYear,&struDownloadCond.struStartTime.dwMonth,
			&struDownloadCond.struStartTime.dwDay,&struDownloadCond.struStartTime.dwHour,&struDownloadCond.struStartTime.dwMinute,
			&struDownloadCond.struStartTime.dwSecond);
	//结束时间
	sscanf(end, "%4d%2d%2d%2d%2d%2d",&struDownloadCond.struStopTime.dwYear,&struDownloadCond.struStopTime.dwMonth,
			&struDownloadCond.struStopTime.dwDay,&struDownloadCond.struStopTime.dwHour,&struDownloadCond.struStopTime.dwMinute,
			&struDownloadCond.struStopTime.dwSecond);


	//按时间下载
	int hPlayback = NET_DVR_GetFileByTime_V40(userId, fileName, &struDownloadCond);
	if(hPlayback < 0){
		printf("NET_DVR_GetFileByTime_V40 fail,last error %u\n",NET_DVR_GetLastError());
		return 0;
	}
	//---------------------------------------
	//开始下载
	if(!NET_DVR_PlayBackControl_V40(hPlayback, NET_DVR_PLAYSTART, NULL, 0, NULL,NULL)){
		cout<<"Play back control failed "<<NET_DVR_GetLastError()<<endl;
  		return 0;
	}

	//判断文件是否存在
	fstream _file;
	_file.open(fileName, ios::in);
	while(!_file){
		usleep(200000);
	}
	char *buf=(char *)malloc(sizeof(char)*20);
	char cmd[150];
	strcat(cmd,"/usr/bin/mediainfo  \"--Inform=General;%Duration/String3% %FileSize%\" ");
	strcat(cmd,fileName);
	long int curSize=0,lastSize;
	int duration;
	DWORD speed;
	while(true){
		usleep(500000);
		getCmd(cmd, buf);
		sscanf(buf,"%d:%ld", &duration, &curSize);
		if(curSize==lastSize) break;
		lastSize=curSize;
		if(num <= 1){
			if(duration >= totalDuration) break;
			else if(totalDuration- duration < 400){
				speed=256*pow(32,(totalDuration-duration)/200.0);
				NET_DVR_PlayBackControl_V40(hPlayback, NET_DVR_SETSPEED, &speed , 0, NULL, NULL);
			  }
		  }
		  cout<<"progress is:"<<100*duration/totalDuration<<"%"<<endl;
	  }
	  cout<<"progress is:100%"<<endl;
	  free(buf);
	  if(!NET_DVR_StopGetFile(hPlayback)){
	      cout<<"failed to stop get file "<<NET_DVR_GetLastError()<<endl;
	      return 0;
	  }
	  return 1;
}
void getCmd(char * cmd, char *res){
	char buf[100], *size;
	size=(char *)malloc(sizeof(char)*20);
	int h,m;
	float s;
	FILE *file = popen(cmd, "r");      /*子进程执行 ls -la ,并把输出写入管道中*/
	if(!feof(file)){
		fgets(buf, 100, file);
		sscanf(buf,"%d:%d:%f %s",&h,&m,&s,size);

		sprintf(res,"%d:%s",h*3600+m*60+(int)s,size);
	}
	pclose(file);
	free(size);
}

void CALLBACK DisplayCBFun(int nPort,char * pBuf, int nSize,int nWidth,int nHeight,int nStamp,int nType,int nReserved){

	//判断针对当前视频文件是否已经抓图
	fstream _file;
	_file.open(destPath, ios::in);
	if(_file){//如果图片文件已经存在 说明已经抓取成功
		return;
	}

	if(!PlayM4_ConvertToJpegFile(pBuf,nSize,nWidth,nHeight,nType,
		destPath)){
		printf("convert to jpeg fail. [%d]\n", PlayM4_GetLastError(nPort));
		return;
	}else{
		fstream _file;
		_file.open(destPath, ios::in);
		while(!_file){
			usleep(20000);
		}
		printf("save success.\n");
		if(nPort){
			//停止解码
			PlayM4_Stop(nPort);
			//关闭文件
			PlayM4_CloseStream(nPort);
			//释放端口号
			PlayM4_FreePort(nPort);
		}

		nPort = -1;//恢复默认值
		printf("exit...");
		state = 1;
		exit(0); //一旦保存成功 直接退出
	}
	return;

}

void CALLBACK f_PlayDataCallBack_V40(LONG lPlayHandle, DWORD dwDataType, BYTE *pBuffer, DWORD dwBufSize, void* dwUser){

	LONG dwError = 0;
	int bRet;
	switch (dwDataType){
        case NET_DVR_SYSHEAD: //文件头
			if(nPort == -1){
				if(!PlayM4_GetPort(&nPort)){
					printf("get nport fail. [%d]\n", PlayM4_GetLastError(nPort));
					return ;
				}
			}
			//设置流模式
			bRet = PlayM4_SetStreamOpenMode(nPort, STREAME_FILE);
			if(!bRet){
				printf("set stream mode fail [%d]\n", PlayM4_GetLastError(nPort));
				return;
			}
			if(dwBufSize > 0){
				//打开流
				if(!PlayM4_OpenStream(nPort, pBuffer, dwBufSize, 1024*10000)){
					printf("open stream fail. [%d]\n", PlayM4_GetLastError(nPort));
					return;
				}
			}
			//设置显示回调
			if(!PlayM4_SetDisplayCallBack(nPort, DisplayCBFun)){
				printf("set displayCallBack fail. [%d]\n", PlayM4_GetLastError(nPort));
				return;
			}

			if(!PlayM4_Play(nPort, hWnd)){
				printf("play stream fail. [%d]\n", PlayM4_GetLastError(nPort));
				return;
			}

			break;
        case NET_DVR_STREAMDATA:  //码流数据
			while(1){
					BOOL bFlag = PlayM4_InputData(nPort, pBuffer, dwBufSize);
					if(!bFlag){
						dwError = PlayM4_GetLastError(nPort);
						if(dwError == 11){ //缓冲区满 输入流失败 需重复送入数据
							sleep(2);
							continue;
						}
					}
					break; //若送入成功,则继续读取数据到播放库缓冲
			}
	}
}

int getPictureByFileName(int userId, char * srcfile, char * destfile){

	fstream _file;
	_file.open(destPath, ios::in);
	if(_file){//如果已经存在 说明已经抓取成功
		printf("destpath is already exist, can not save, please reset destpath\n");
		return 0;
	}

	LONG hPlayback = 0;

	if(( hPlayback = NET_DVR_PlayBackByName(userId, srcfile, 0)) < 0 ){
		cout<<"Error: "<<NET_DVR_GetLastError()<<endl;
		return 0;
	}
	//设置回调函数
	if(!NET_DVR_SetPlayDataCallBack_V40(hPlayback, f_PlayDataCallBack_V40, NULL)){
		printf("set callback failed [%d]\n", NET_DVR_GetLastError());
	}
	//开始下载
	if (!NET_DVR_PlayBackControl_V40(hPlayback, NET_DVR_PLAYSTART, NULL, 0,
			NULL, NULL)) {
		printf("play back control failed [%d]\n", NET_DVR_GetLastError());
		return 0;
	}

	sleep(100);
	//停止回放
	if(!NET_DVR_StopPlayBack(hPlayback)){
		cout<<"stop playback file failed: "<<NET_DVR_GetLastError()<<endl;
		return 0;
	}
	if(nPort){
		//停止解码
		PlayM4_Stop(nPort);
		//关闭文件
		PlayM4_CloseStream(nPort);
		//释放端口号
		PlayM4_FreePort(nPort);
	}
	return 1;
}
int saveFileByName(int userId, char * srcfile, char * destfile) {
	int hPlayback = 0;
	//按文件名下载录像
	if ((hPlayback = NET_DVR_GetFileByName(userId, srcfile, destfile)) < 0) {
		printf("GetFileByName failed. error[%d]\n", NET_DVR_GetLastError());
		return 0;
	}
	//开始下载
	if (!NET_DVR_PlayBackControl_V40(hPlayback, NET_DVR_PLAYSTART, NULL, 0,
			NULL, NULL)) {
		printf("play back control failed [%d]\n", NET_DVR_GetLastError());
		return 0;
	}

	int nPos = 0;
	DWORD time = 0;
	for (nPos = 0; nPos < 100 && nPos >= 0; nPos = NET_DVR_GetDownloadPos(hPlayback)) {
		NET_DVR_PlayBackControl_V40(hPlayback, NET_DVR_GETTOTALTIME, NULL, 0,&time, NULL);
		printf("Be downloading...%d %% the time is %d\n", nPos, time); //下载进度
		usleep(200000); //millisecond
	}
	printf("have got %d%%\n", nPos);
	//停止下载
	if (!NET_DVR_StopGetFile(hPlayback)) {
		printf("failed to stop get file [%d]\n", NET_DVR_GetLastError());
		return 0;
	}

	if (nPos < 0 || nPos > 100) {
		printf("download err [%d]\n", NET_DVR_GetLastError());
		return 0;
	}
	return 1;
}
/*
 * 不支持
 *
 */
void getStartAndEndTimeForIpChannel(LONG lUserID, DWORD dwChannel){
	NET_DVR_RECORD_TIME_SPAN_INQUIRY lpInquiry;
	NET_DVR_RECORD_TIME_SPAN lpResult;
	lpInquiry.byType = '0';
	lpInquiry.dwSize = sizeof(NET_DVR_RECORD_TIME_SPAN_INQUIRY);

	BOOL flag = NET_DVR_InquiryRecordTimeSpan(lUserID, dwChannel, &lpInquiry, &lpResult);
	if(flag){
		cout<<lpResult.dwSize<<" "<<getTime(lpResult.strBeginTime)<<" "<<getTime(lpResult.strEndTime)<<" "<<lpResult.byType<<endl;
	}else{
		cout<<"GETLastError "<<NET_DVR_GetLastError()<<endl;
	}
}

int main(int argc, char *args[]){

	LONG userId=login(args[1], atoi(args[2]), args[3], args[4]);
	if(userId<0)return 0;

	if(!strcmp(args[5],"list"))
		state = listCammera(userId);
	else if(!strcmp(args[5],"download")){
		if(argc==10)
			state = dowload(userId, args[6], args[7],atol( args[8]),args[9]);
		else
			state = saveFileByName(userId, args[6], args[7]);
	}else if(!strcmp(args[5],"queryBlock")){
		state = findFileBytimeAndIpChannle(userId,args[6], args[7],atol( args[8]));
	}else if(!strcmp(args[5], "getPicture")){
		strcpy(destPath, args[7]);
		getPictureByFileName(userId, args[6], destPath);
	}

	if(!strcmp(args[5], "getPicture") && state == 0){
		printf("getPicture fail.\n");
	}
	printf("exit...");


	//注销用户
	NET_DVR_Logout(userId);
	//释放SDK资源
	NET_DVR_Cleanup();
	exit(0);

	/*
	 *example:
	 * getStartAndEndTimeForIpChannel(1, -1);//设备不支持
	 * findFileBytimeAndIpChannle(userId, "20000413101055", "20161005120000", 33);
	 * dowload(userId, "20160906120000", "20161005120000", 33, "/home/gyy/data/2016");
	 * saveFileByName(userId, "ch01_03000000975000200", "/home/gyy/data/test.avi");
	*/

}
