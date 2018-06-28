#!/bin/bash

node=10
val=$(ls -dq *results* | wc -l)
val="$(($val-1))"
total=$(for i in $(seq 0 $val); do cat results.txt_$i |grep Total | awk '{print $4}';done)
response=$(for i in $(seq 0 $val); do cat results.txt_$i |grep Res |awk '{print $4}'; done)
th=$( for i in $(seq 0 $val); do cat results.txt_$i |grep Th |awk '{print $3/1024}'; done)


paste <(echo "Througput(GB/s)") <(echo "Run Time") <(echo "AVG Response") --delimiters '\t'
paste <(echo "$th") <(echo "$total") <(echo "$response") --delimiters '\t'


miss=''
for (( i = 0; i < node; i++ ))
do
   	var="1-$i"
   	arr[$i]=$(for i in $(seq 0 $val); do cat results.txt_$i |grep ${var}| awk '{print $4}';done)

done

echo "Hit Ratios"

for (( i = 0; i < node; i++ ))
do
        var="2-$i"
        arr2[$i]=$(for i in $(seq 0 $val); do cat results.txt_$i |grep ${var}| awk '{print $4}';done)
done

miss="paste "
for (( i = 0; i < node; i++ ))
do
a="<(echo \"\${arr[$i]}\") "
miss=$(echo "$miss$a")
done
for (( i = 0; i < node; i++ ))
do
a="<(echo \"\${arr2[$i]}\") "
miss=$(echo "$miss$a")
done

a="--delimiters '\t'" 
miss=$(echo "$miss$a")
eval $miss

echo "L1 Miss Ratio"

for (( i = 0; i < $val; i++ ))
do
	 cat results.txt_$i |grep "1-"| awk '{ total += $4 } END { print total/NR }' 	
done

echo "L2 Miss Ratio"

for (( i = 0; i < $val; i++ ))
do
	 cat results.txt_$i |grep "2-"| awk '{ total += $4 } END { print total/NR }' 	
done

