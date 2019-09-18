#! /usr/bin/bash
MODE=""
MATHINEIP=""
SLAVEIP=""
MT4MANAGERADDR=""
MT4MANAGERACCOUNT=""
MT4MANAGERPASSWORD=""
TIMEZONE=""

TRADEHOOK="true"
HOOKADDR=""
HOOKPORT=""
TRADESOURCE="followtrade"

# ./initLinux.sh --mode single --master_addr 192.168.80.129 --mt4_addr 35.200.34.24:443 --mt4manager_account 88 --mt4manager_password X@4MxUY*5486 --timezone 2 --hook_addr risk-dev.dealer-internal.com --hook_port 3001 --trade_source 88-demo

# docker ps -a |awk '{if(NR>1){print $1}}'|xargs -I {}  docker rm -f {}


if [ $(uname -s) != Linux ];then
    echo "ERROR: you need a Linux Server"
    exit 1
fi

function show_use(){
	echo "
FollowTrade v1.0   Copyright  WHHL.
usage:
	--mode
		for install mode [ --mode master | --mode slave | --mode single ]
	--master_addr
		for master ip address
	--slave_addr
		for slave ip address
	--mt4_addr
		for mt4 manager ip address and port
	--mt4manager_account
		for mt4 manager account
	--mt4manager_password
		for mt4 manager password
	--timezone
		for timezone config
	--trade_hook
		for tradehook mode (add riskcontrol) Default:[ --trade_hook true ]
	--hook_addr
		for hook server ip address or url
	--hook_port
		for hook server port
	--trade_source
		for hook source config  Default:[ --trade_source followtrade ]
	example:
	   [bash]./initLinux.sh --mode master --master_addr xxx --slave_addr xxx --mt4_addr xxx --mt4manager_account xxx --mt4manager_password xxx \\
	   		--timezone 2 --hook_addr xxx.xxx.com --hook_port 1234  --trade_source example

"
}

TEMP=`getopt -o m:a:s:r:e:p:t:k:o:c:h \
--long mode:,master_addr:,slave_addr:,mt4_addr:,mt4manager_account:,mt4manager_password:,timezone:,trade_hook:,hook_addr:,hook_port:,trade_source:,help  \
	-n 'ERROR: ' -- "$@"`
if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi
eval set -- "$TEMP"

while true ; do
    case "$1" in
        -m|--mode)
			MODE="$2"
			shift 2 ;;
        -a|--master_addr)
			MATHINEIP="$2"
			shift 2 ;;
		-s|--slave_addr)
			SLAVEIP="$2"
			shift 2 ;;
		-r|--mt4_addr)
			MT4MANAGERADDR="$2"
			shift 2 ;;
		-e|--mt4manager_account)
			MT4MANAGERACCOUNT="$2"
			shift 2 ;;
		-p|--mt4manager_password)
			MT4MANAGERPASSWORD="$2"
			shift 2 ;;
		-t|--timezone)
			TIMEZONE="$2"
			shift 2 ;;
		-k|--trade_hook)
			TRADEHOOK="$2"
			shift ;;
		-d|--hook_addr)
			HOOKADDR="$2"
			shift 2 ;;
		-o|--hook_port)
			HOOKPORT="$2"
			shift 2 ;;
		-c|--trade_source)
			TRADESOURCE="$2"
			shift 2 ;;
        -h|--help)
        	show_use
			exit 1 ;;
		--) shift
			break ;;
        *)  shift
			break ;;
    esac
done

if [ "$MODE" == "" ];then
	show_use
	echo "ERROR: install mode is required eg：[ --mode master | --mode slave | --mode single ]"
	exit 1
elif [ "$MODE" == "master" ] || [ "$MODE" == "slave" ];then
	if [ "$MATHINEIP" == "" ] || [ "$SLAVEIP" == "" ];then
		show_use
		echo "ERROR: you need add master and slave ip address  eg:[ --master_addr xxx  --slave_addr xxx ]"
		exit 1
	fi
	echo "Notice: Single mode is supported yet.  Exit"
	exit 1
elif [ "$MODE" == "single" ];then
	echo "single mode selected"
	if [ "$MATHINEIP" == "" ];then
		show_use
		echo "ERROR: Single mode ip address is required eg:[ --master_addr xxx ]"
		exit 1
	fi
else
	show_use
	echo "ERROR: install mode is required  eg:[ --mode master | --mode slave | --mode single ]"
	exit 1
fi


if [ "$MT4MANAGERADDR" == "" ];then
	show_use
	echo "ERROR: mt4 manager ip address is required  eg:[ --mt4_addr 123.123.123.123 ]"
	exit 1
fi
if [ "$MT4MANAGERACCOUNT" == "" ];then
	show_use
	echo "ERROR: mt4 manager account is required  eg:[ --mt4manager_account 87236423 ]"
	exit 1
fi
if [ "$MT4MANAGERPASSWORD" == "" ];then
	show_use
	echo "ERROR: mt4 manager password is required  eg:[ --mt4manager_password &^%*(^)%#asf ]"
	exit 1
fi
if [ "$TIMEZONE" == "" ];then
	show_use
	echo "ERROR: timezone is required  eg:[ --timezone 2 ]"
	exit 1
fi
if [ "$TRADEHOOK" == "true" ];then
	if [ "$HOOKADDR" == "" ];then
		show_use
		echo "ERROR: when tradehook is true, hook_addr is required  eg:[ --hook_addr 123.123.123.123 ]"
		exit 1
	fi
	if [ "$HOOKPORT" == "" ];then
		show_use
		echo "ERROR: when tradehook is true, hook_port is required  eg:[ --hook_port 443 ]"
		exit 1
	fi
elif [ "$TRADEHOOK" == "false" ];then
	echo ""
else
	show_use
	echo "ERROR: unknow tradehook (default: true)  eg:[ --trade_hook false ]"
	exit 1
fi

echo " 		______    _ _            _______            _        "
echo " 		|  ____|  | | |          |__   __|          | |      "
echo " 		| |__ ___ | | | _____      _| |_ __ __ _  __| | ___  "
echo " 		|  __/ _ \| | |/ _ \ \ /\ / / | '__/ _\` |/ _\` |/ _ \ "
echo " 		| | | (_) | | | (_) \ V  V /| | | | (_| | (_| |  __/ "
echo " 		|_|  \___/|_|_|\___/ \_/\_/ |_|_|  \__,_|\__,_|\___| "
echo ""
echo "Welcome to use followtrade"
echo "It will take a few minutes to install, be patient width it please...."

function docker_install(){
    echo "check for Docker......"
    docker -v
    if [ $? -eq  0 ]; then
        echo "docker enviroment success!"
    else
    	echo "starting install docker..."
        curl -sSL https://get.daocloud.io/docker | sh
    fi
    echo "check for Docker-compose......"
    docker-compose -v
    if [ $? -eq 0 ]; then
		echo "docker-compose enviroment success!"
    else
		echo "start install docker-compose..."
		curl -fsSL https://get.docker.com/ | sh
    fi	
}

if [ "$TRADEHOOK" == "true" ];then
	echo "use default config   [ --trade_hook true ]"
fi
if [ "$TRADESOURCE" == "followtrade" ];then
	echo "use default config   [ --trade_source followtrade ]"
fi

echo "enviroment check..."
docker_install
echo "======================================================================================"
echo "FOLLOWTRADE Install starting..."
SHPATH=$(cd "$(dirname "$0")";pwd)
docker login -u=user -p="password" aaa.bbb.com
if [ $? -ne 0 ]; then
	echo "docker login failed.... check your server network please."
	exit 1
fi

if [ $MODE == "master" ];then
	#init master consul
	sed -i "s/command: \"agent -server -bootstrap-expect 2 -ui -advertise .*  -client 0.0.0.0\"/command: \"agent -server -bootstrap-expect 2 -ui -advertise $MATHINEIP  -client 0.0.0.0\"/g" $SHPATH/consul/master/docker-compose.yml
	sed -i "s/command: \"agent -server  -retry-join .*  -client 0.0.0.0\"/command: \"agent -server  -retry-join $MATHINEIP  -client 0.0.0.0\"/g" $SHPATH/consul/master/docker-compose.yml
    cd $SHPATH/consul/master && docker-compose up -d
    #init master redis
    sed -i "s/sentinel monitor followtrade .* 6379 2/sentinel monitor followtrade $MATHINEIP 6379 2" $SHPATH/redis-sentinel/slave/sentinel.conf
    cd $SHPATH/redis-sentinel/master && docker-compose up -d
    #init master nats
    sed -i "s/- \".*:4223\"/- \"$MATHINEIP:4223\"/g"  $SHPATH/nats/master/docker-compose.yml
    sed -i "s/- \".*:6223\"/- \"$MATHINEIP:6223\"/g"  $SHPATH/nats/master/docker-compose.yml
    sed -i "s/- \"nats:\/\/.*:6222\"/- \"nats:\/\/$MATHINEIP:6222\"/g"  $SHPATH/nats/master/docker-compose.yml
    cd $SHPATH/nats/master && docker-compose up -d
elif [ $MODE == "slave" ];then
	#init slave consul
	sed -i "s/command: \"agent -server -bootstrap-expect 2  -retry-join .* -advertise .*\"/command: \"agent -server -bootstrap-expect 2  -retry-join $MATHINEIP -advertise $MATHINEIP\"/g" $SHPATH/consul/slaver/docker-compose.yml
    cd $SHPATH/consul/slaver && docker-compose up -d

    #init slave master
    sed -i "s/slaveof .* 6379/slaveof $MATHINEIP 6379/g" $SHPATH/redis-sentinel/slave/redis.conf
	sed -i "s/sentinel monitor followtrade .* 6379 2/sentinel monitor followtrade $MATHINEIP 6379 2" $SHPATH/redis-sentinel/slave/sentinel.conf
    cd $SHPATH/redis-sentinel/slave && docker-compose up -d
    #init nats slave
    sed -i "s/- \".*:4223\"/- \"$SLAVEIP:4223\"/g"  $SHPATH/nats/slaver/docker-compose.yml
    sed -i "s/- \".*:6223\"/- \"$SLAVEIP:6223\"/g"  $SHPATH/nats/slaver/docker-compose.yml
    sed -i "s/- \"nats:\/\/.*:6222\"/- \"nats:\/\/$SLAVEIP:6222\"/g"  $SHPATH/nats/slaver/docker-compose.yml
    cd $SHPATH/nats/slaver && docker-compose up -d
elif [ $MODE == "single" ];then
	sed -i "s#command: \"agent -server   -node masters2  -bootstrap-expect 1 -ui -advertise .* -client 0.0.0.0 -datacenter kvb -log-file /log/server1-consul.log\"#command: \"agent -server   -node masters2  -bootstrap-expect 1 -ui -advertise $MATHINEIP -client 0.0.0.0 -datacenter kvb -log-file /log/server1-consul.log\"#g" $SHPATH/consul/single/docker-compose.yml
	cd $SHPATH/consul/single && docker-compose up -d
    cd $SHPATH/redis-sentinel/single && docker-compose up -d
    cd $SHPATH/nats/single && docker-compose up -d
fi

cd $SHPATH/trade-web/ && docker-compose up -d

CONTAINERID=$(docker ps | grep redis |awk '{print $1}')

if [ "$CONTAINERID" == "" ];then
	echo "redis server down, exit."
	exit 1
fi

if [ $MODE == "master" ] || [ $MODE == "single" ];then

	docker exec $CONTAINERID  redis-cli -h 127.0.0.1 -p 6379 -a myredis hset tradeapi:storage:broker-infos "8"  "{\"ID\":8,\"ProtocolType\":0,\"ServerName\":\"demo\",\"Addresses\":[\"\"],\"AgentType\":1,\"AgentServiceName\":\"pure.trade-agent.mt4dealer-8\",\"Group\":\"\"}"
	if [ $? -ne 0 ];then
		echo "ERROR: redis config init failed...."
		exit 1
	fi
	curl -X PUT http://$MATHINEIP:8500/v1/kv/SymbolWatchKey -d '1543325331'
	if [ $? -ne 0 ];then
		echo "ERROR: watch-key consul config init failed...."
		exit 1
	fi
	curl -X PUT http://$MATHINEIP:8500/v1/kv/trade-api -d '
	{
	    "service-name" : "followme.trade-api",
		"http-addr" : ":8702",
	    "nats-url" : "followtrade:XONhKiELUuh6xozh@'$MATHINEIP':4222", 
	    "redis" : {
	        "host" : "127.0.0.1:6379",
	        "pwd" : "myredis"
	    },
	    "default-symbol" :["AUDCAD","HSI43"],
	    "mgr-token" : "followmemgrtoken",
	    "company-name": "kvb",
	    "site-domain-name": ".followme.cn",
		"allow-origins": ["http://'$MATHINEIP':8702"],
	    "watch-key" : "hello, followme."
	}'
	if [ $? -ne 0 ];then
		echo "ERROR: trade-api consul config init failed...."
		exit 1
	fi
	curl -X PUT http://$MATHINEIP:8500/v1/kv/pure-mt4dealer-8 -d '
	{
	   "service-name": "pure.trade-agent.mt4dealer",
	   "master-service-name": "followme.trade-api",
	   "address": "'$MT4MANAGERADDR'",
	   "account": '$MT4MANAGERACCOUNT',
	   "password": "'$MT4MANAGERPASSWORD'",
	   "timezone": '$TIMEZONE',
	   "jaeger-url": "'$MATHINEIP':6831",
	   "action-async":true,
	   "trade-hook":'$TRADEHOOK',
	   "trade-source":"'$TRADESOURCE'",
	   "hook-server-name":"followme.srv.copytrade.risk.kvbprime"
	}'
	if [ $? -ne 0 ];then
		echo "ERROR: dealer consul config init failed...."
		exit 1
	fi
fi

sed -i "s/- CONSUL_HTTP_ADDR=.*:8500/- CONSUL_HTTP_ADDR=$MATHINEIP:8500 6379/g" $SHPATH/trade-api/docker-compose.yml
cd $SHPATH/trade-api/ && docker-compose up -d

if [ $MODE == "master" ] || [ $MODE == "single" ];then
	curl -X PUT http://$MATHINEIP:8500/v1/agent/service/register -d '
	{
		"ID": "followme.srv.copytrade.risk.kvbprime-14077694-d2cb-11e9-8b18-acde48001122",
		"Name": "followme.srv.copytrade.risk.kvbprime",
		"Tags": ["v-1.0.0"],
		"Port": '$HOOKPORT',
		"Address": "'$HOOKADDR'",
		"Checks": null
	}'
	if [ $? -ne 0 ];then
		echo "ERROR: hook service consul config init failed...."
		exit 1
	fi
fi

docker logout aaa.bbb.com
echo "All has down success"
echo "======================================================================================"


