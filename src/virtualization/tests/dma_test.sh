modprobe dmatest
modprobe idxd_ktest
DMA_TEST_PATH=/sys/module/dmatest/parameters

echo 10000 > $DMA_TEST_PATH/iterations
echo 0 > $DMA_TEST_PATH/noverify
echo 1 > $DMA_TEST_PATH/verbose
echo 0 > $DMA_TEST_PATH/alignment
echo 0 > $DMA_TEST_PATH/norandom
#echo 1048576 > $DMA_TEST_PATH/test_buf_size
#echo 524288 > $DMA_TEST_PATH/transfer_size
echo 8 > $DMA_TEST_PATH/threads_per_chan
echo " " > $DMA_TEST_PATH/channel
echo 1 > $DMA_TEST_PATH/run
