#!/bin/bash
# ffmpeg_edit.sh - FFmpeg fallback batch script

EPISODE_ID=$1
HOST_VIDEO="${WATCH_FOLDER}${EPISODE_ID}/host.mp4"
MUSIC="${BUILD_FOLDER}${EPISODE_ID}/music.wav"
INTRO="${ASSETS_FOLDER}templates/intro.mov"
OUTRO="${ASSETS_FOLDER}templates/outro.mov"
OUTPUT="${BUILD_FOLDER}${EPISODE_ID}/final.mp4"

# Concatenate videos and add music
ffmpeg -i $INTRO -i $HOST_VIDEO -i $OUTRO -i $MUSIC -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v];[3:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a]" -map "[v]" -map "[a]" $OUTPUT

echo "Edited video saved to $OUTPUT"