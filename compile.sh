g++ -IincCn -O0 -g3 -Wall -c -fmessage-length=0 -ohiktool.o hik.cpp
g++ -L/lib64/ -ohik hiktool.o -lhcnetsdk -lPlayCtrl -lSuperRender -lAudioRender
