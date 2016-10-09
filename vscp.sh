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
    local RTSPID=$1
    local DIRNAME=$2

    STARTCMD="ffmpeg -i rtsp://admin:632911632@10.103.242.105:554/PSIA/streaming/channels/$RTSPID -c copy -map 0 -f segment -strftime 1 -segment_time 300 -segment_format flv $BASE_DIR/$DIRNAME/$DIRNAME-%Y-%m-%d-%H-%M-%S.flv"
    echo $STARTCMD
    (
    `${STARTCMD}`
    ) &
    SUB_PROCESS_FFMPEG[$RTSPID]=$!
}


while true
do
    if ping -c 1 -w 2 baidu.com &>/dev/null
    then
        :
    else
        echo "[NETWORK ERROR] please connect to internet! [/NETWORK ERROR]" >> process.log
        sleep 5m
        continue
    fi

    if ping -c 1 -w 2 ${NVR_URL} &> /dev/null
    then
        :
    else
        echo "[CONNECT ERROR] can not connect $NVR_URL, please confirm whether if opened. [/CONNECT ERROR]" >> process.log
        sleep 5m
        continue
    fi

    for LINE in  `${LISTCAMERACOMMOND}`
    do
        CHANNELID=`echo $LINE | awk -F ',' '{ print $1 }' | awk -F ':' '{ print $2 }'`
        IPADDR=`echo $LINE | awk -F ',' '{ print $2 }' | awk -F ':' '{ print $2 }'`

        RTSP_ID=$(((CHANNELID+1)*100+1))
        CURRENT_IDLIST=`echo ${!CHANNELIST[@]}` # get all ipadder in currentlist array ( the ipadder in currentlist is the ip have already being processed)



        # if current channel is active

        if echo $LINE | grep 'channel' > /dev/null
        then
            # each channel have a dir for storge the video file correspond to it
            # if not exist dir for it , creat dir for it , the dir name is channelid eg: ch101, ch201

            DIR_NAME=`echo ch"$RTSP_ID"`
            if [ ! -d "$BASE_DIR/$DIR_NAME" ];then
                mkdir "$BASE_DIR/$DIR_NAME"
            fi
            
            # if not in channelist, array add to channelist and start new job for current channel id

            if [ "no" = `is_arrayhasitem "$CURRENT_IDLIST" "$CHANNELID"` ]
            then
                CHANNELIST[$CHANNELID]=$IPADDR
                ((++TOTAL))
                start_job_func $RTSP_ID $DIR_NAME
                echo "[START][CHANNEL ID : "$RTSP_ID"] start processing channel "$RTSP_ID" : "$IPADDR" by child process "${SUB_PROCESS_FFMPEG[$RTSP_ID]}" . [/START]" >> process.log # write info to log
            else
                # if channelid is already in list , get the process id and judeg if it aleady dead
                # if has dead, restart new job for current channelid and update the value of CHANNELIST[$CHANNELID]
                SUB_FFMPEG_PROCESS_ID=${SUB_PROCESS_FFMPEG[$RTSP_ID]}
                if [ "0" = `ps --no-heading "$SUB_FFMPEG_PROCESS_ID" | wc -l` ]
                then
                    start_job_func $RTSP_ID $DTR_NAME
                    CHANNELIST[$CHANNELID]=$IPADDR
                    echo "[RESTART][CHANNEL ID: "$RTSP_ID"] restart processing "$TRSP_ID" : "$IPADDR"  by child process "${SUB_PROCESS_FFMPEG[$RTSP_ID]}". [/RESTART]" >> process.log
                fi
            fi
        else
            # if current channel is not active
            # look up chnnelist , if current channel is in ,delete it

            if [ "yes" = `is_arrayhasitem "$CURRENT_IDLIST" "$CHANNELID"` ]
            then
                unset CHANNELIST[$CHANNELID]
                unset SUB_PROCESS_FFMPEG[$RTSP_ID]

                echo "[DELETE][CHANNEL ID : "$RTSP_ID"] channel "$RTSP_ID" is not active now, delete it from CURRENTLIST [/DELETE]" >> process.log
                ((--TOTAL))
            fi
        fi
    done
    sleep 1m # loop every 1 minutes
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
