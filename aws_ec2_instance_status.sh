printf "\nLooking for EC2 instances\n"
printf "*********************************************************************************************************************\n"
ID_LIST1=$(aws ec2 describe-instances --filters Name=instance-state-name,Values=running,stopped | grep InstanceId | awk
'{printf "%s", $2}')
ID_LIST2=${ID_LIST1//\"} #Get rid of the double quotes
ID_LIST3=${ID_LIST2//\,/ } #Replace the comma with a space
if [ "x$ID_LIST3" = "x" ]; then
 printf "No instances found to be listed\n"
else
  printf "Listing instances $ID_LIST3"
fi
