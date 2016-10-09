# vscp-backend
backend file for VSCP project

1. **vsch.sh:** Real time monitor and access to Hikvision's video streaming data for every active video channel, Segment stream data every 5 minutes period, auto create local directory according to the channel name and storage the created video file(.flv) to the local temporary file directory.
2. **uploadVideoToHDFS:** the python script in this directory is mainly for monitoring the new video files in current tmp local directory(all in data directory) for every Hikvision video channel and upload them to remote hdfs system.
3. **hik.cpp:**  Underlying interface for acquiring related equipment and video information of Hikvision network equipment, realizing based on the Hikvision SDK using C Language.
