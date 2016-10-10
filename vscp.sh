#!/bin/bash


##################################################################
# author gyy                                                     #
# created 2016.10.2                                              #
##################################################################

# declare a associative array : key -> channelid value -> ipadder
declare -A CHANNELIST

TOTAL=0

LISTCAMERACOMMOND='./hik 10.103.242.105 8000 admin 632911632 list'

URL_PREFIX='rtsp://admin:632911632@10.103.242.105:554/PSIA/streaming/channels/'
NVR_URL='10.103.242.105'

BASE_DIR='./data'


######################  tool function ########################


# get current system date
get_date(){
    echo "[`date "+%G-%m-%d %H:%M:%S"`]"
}
# judge if elem in array
is_arrayhasitem(){
    local ARRAY_TMP;
    ARRAY_TMP=`echo "$1"`

    for item in ${ARRAY_TMP[*]}
    do
        if [ "$2" = "$item" ]
        then
            echo yes
            return
        fi
    done
    echo no
}

################## tool function end #########################


# stroge pid for child work process

declare -A SUB_PROCESS_FEMPEG

start_job_func()
{
    RTSPID=$1
    DIRNAME=$2

    sleep 1s
    STARTCMD="ffmpeg -i rtsp://admin:632911632@10.103.242.105:554/PSIA/streaming/channels/$RTSPID -c copy -map 0 -f segment -strftime 1 -segment_time 300 -segment_format flv $BASE_DIR/$DIRNAME/$DIRNAME-%Y-%m-%d-%H-%M-%S.flv"
    
    (
    `${STARTCMD}`
    ) &
    # $i is current sub process pid , this shell is responsible to run ffmpeg commond , each sub shell run only one ffmepg
    CURRENT_SUB_SHELL_PROCESS_ID=$!
    sleep 2s
    #The following two statements are used to obtain the PID of the current ffmpeg commond process
    CURRENT_FFMPEG_PROCESS_INFO=`ps -lA | grep ffmpeg | sed -n "/$CURRENT_SUB_SHELL_PROCESS_ID/p" | sed 's/[[:space:]][[:space:]]*/ /g'` # this ffmepg commond is the only process running in CURRENT_SUB_SHELL_PROCESS
    CURRENT_FFMPEG_PROCESS_PID=`echo $CURRENT_FFMPEG_PROCESS_INFO | cut -d ' ' -f 4`
    #arr=(`echo $CURRENT_FFMPEG_PROCESS_INFO | awk '{ split($0, a," ");print a[4],a[5]}'`)
    SUB_PROCESS_FFMPEG[$RTSPID]=$CURRENT_FFMPEG_PROCESS_PID
}


while true
do
    if ping -c 1 -w 2 ${NVR_URL} &> /dev/null
    then
        :
    else
        echo "`get_date`[CONNECT ERROR] can not connect $NVR_URL, please confirm whether if opened. [/CONNECT ERROR]" >> process.log
        sleep 5m
        continue
    fi

    for LINE in  `${LISTCAMERACOMMOND}`
    do
        if echo $LINE | grep 'IP' >/dev/null 2>&1
        then
            CHANNELID=`echo $LINE | cut -d "," -f 1 | cut -d ':' -f 2`
            RTSP_ID=$(((CHANNELID+1)*100+1))
            DIR_NAME=`echo ch"$RTSP_ID"`
            # if current channel is active

            if echo $LINE | grep 'channel' > /dev/null
            then
                IPADDR=`echo $LINE | cut -d "," -f 2 | cut -d ':' -f 2`
                CURRENT_RTSP_ID_LIST=`echo ${!CHANNELIST[@]}` # get all ipadder in currentlist array ( the ipadder in currentlist is the ip have already being processed)

                # each channel have a dir for storge the video file correspond to it
                # if not exist dir for it , creat dir for it , the dir name is channelid eg: ch101, ch201

                if [ ! -d "$BASE_DIR/$DIR_NAME" ];then
                    mkdir "$BASE_DIR/$DIR_NAME"
                fi
                # if not in channelist, array add to channelist and start new job for current channel id

                if [ "no" = `is_arrayhasitem "$CURRENT_RTSP_ID_LIST" "$RTSP_ID"` ]
                then
                    CHANNELIST[$RTSP_ID]=$IPADDR
                    ((++TOTAL))
                    start_job_func $RTSP_ID $DIR_NAME
                    echo "`get_date`[START][CHANNEL ID : "$RTSP_ID"] start processing channel "$RTSP_ID" : "$IPADDR" by child process "${SUB_PROCESS_FFMPEG[$RTSP_ID]}" . [/START]" >> process.log # write info to log
                else
                    # if channelid is already in list , get the process id and judeg if it aleady dead
                    # if has dead, restart new job for current channelid and update the value of CHANNELIST[$CHANNELID]
                    SUB_FFMPEG_PROCESS_ID=${SUB_PROCESS_FFMPEG[$RTSP_ID]}
                    if [ 0 -eq `ps --no-heading "$SUB_FFMPEG_PROCESS_ID" | wc -l` ]
                    then
                        CHANNELIST[$RTSP_ID]=$IPADDR

                        start_job_func $RTSP_ID $DIR_NAME
                        echo "`get_date`[RESTART][CHANNEL ID: "$RTSP_ID"] restart processing "$RTSP_ID" : "$IPADDR"  by child process "${SUB_PROCESS_FFMPEG[$RTSP_ID]}". [/RESTART]" >> process.log
                    fi
                fi
            else
                # if current channel is not active
                # look up chnnelist , if current channel is in ,delete it

                if [ "yes" = `is_arrayhasitem "$CURRENT_RTSP_ID_LIST" "$RTSP_ID"` ]
                then
                    unset CHANNELIST[$CHANNELID]
                    SUB_FFMPEG_PROCESS_ID=${SUB_PROCESS_FFMPEG[$RTSP_ID]}
                    if [ 0 -ne `ps --no-heading "$SUB_FFMPEG_PROCESS_ID" | wc -l` ];then
                        kill -9 $SUB_FFMPEG_PROCESS_ID > /dev/null 2>&1
                    fi
                    unset SUB_PROCESS_FFMPEG[$RTSP_ID]
                    echo "`get_date`[DELETE][CHANNEL ID : "$RTSP_ID"] channel "$RTSP_ID" is not active now, delete it from CURRENTLIST [/DELETE]" >> process.log
                    ((--TOTAL))
                fi
            fi
        fi
    done
    sleep 2m # loop every 1 minutes
done

wait # wait sub process all died before exit

# kill all child process before parent process exit

echo "main process exit..." >> process.log

CHILDPROCESSLIST=`echo ${SUB_PROCESS_FFMPEG[@]}`
for ID in ${CHILDPROCESSLIST[@]}
do
    if [ "1" = `ps --no-heading "$ID" | wc -l` ];then
        `ps kill -9 "$ID" > /dev/null`
    fi
done
