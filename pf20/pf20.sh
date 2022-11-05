#!/bin/sh

# This is a simple shell script to start/restart the petfeeder.py
# This gets invoked from CRON  at reboot and continues to run forever

WORKING_DIR=/home/pi/pf20
INTERPRETER=venv/bin/python
COMMAND=pf20.py
LOGFILE=${WORKING_DIR}/data/pf20.startup.log
COMMANDLOG=${WORKING_DIR}/data/pf20.log
COMMANDERR=${WORKING_DIR}/data/pf20.err

writelog() {
        now=`date`
        echo "$now $*" >> $LOGFILE
}

# Wait till our network is up. Sometimes it isn't right after a reboot
#writelog "Checking on network"
#while ! ifconfig | grep -F "192.168.1." > /dev/null 
#do
#	writelog "Waiting on network to come up"
#	# Do nothing, just wait
#        sleep 5
#done


# A generic wait for service like nework to come up
sleep 10

writelog "Starting"
while true 
do
        cd ${WORKING_DIR}; ${INTERPRETER} ${COMMAND} >> $COMMANDLOG 2>> $COMMANDERR
        writelog "Exited with status $?"
        writelog "Restarting"
done

