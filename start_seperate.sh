pkill python
export PATH=/home/ta/anaconda3/bin/:$LD_LIBRARY_PATH
cd /home/ta/Downloads/Number/3/protect/new/624-new
(python -u queue_founder.py &>> seperate_log_queue.log &)
sleep 1
(python -u capture_seperate.py 0 &>> seperate_log_above.log &)
(python -u capture_seperate.py 1 &>> seperate_log_front.log &)

(python -u control_main.py &>> seperate_log_control.log &)


(python -u detect_seperate.py 0 &>> seperate_log_detect_above.log &)
(python -u detect_seperate.py 1 &>> seperate_log_detect_front.log &)
sleep 1

python user_interface_seperate.py
#chmod a-r *.py
