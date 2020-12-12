import urllib.request
import urllib.parse
import os
import sys
import socket
import signal
import time
import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from multiprocessing import Process, Manager
from threading import Thread

CMD = '''
Welcome to use media schedule system benchmark  V1.0beta
you can use it for example：
    python benchmark.py  [CMD]  [Option]
    CMD:
        start       : start benchmark
        init        : to generate login user data
        clean       : clean all group member relations
    
    Option:
        start option:
            start  100(int) 1000(int)    启动100个进程， 每个进程发送1000条数据
        init option:
            init 1000(int)  生成1000个编码资源和1000个解码资源配置


注意：自测回调web服务使用多进程模型，并发100的时候CPU飙升100%，
使用多线程模型,受到GIL锁影响，瞬时并发100大概有10%的请求将会被系统自动关闭。
若使用Cpython解释器的时候，请适当增加backlog参数，提高本地回调性能
或者使用gevent实现多进程异步，或者使用其他语言实现回调服务。

notifyService 是用rust实现的一个简单的回调服务器，用于接收资源成功，
可执行文件在notifyService/target/src/debug/notifyService.exe
'''

config = {
    "MediaCoreAddr": "18.55.10.130:31490",      # multi-controller-service地址
    "SipAccountStart": 60000000000,             # 生成sip账号的起始编号
    "SelfAddr": "127.0.0.1:6666"                # 创建资源成功后，回调的地址
}

DEFAULT_HTTP_HEADER = {
    "User-Agent": "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",
    "Content-Type": "application/json"
}


class Notify(BaseHTTPRequestHandler):
    """
    异步回调http服务,  内置BaseHTTPRequestHandler为单进程阻塞 无法并发弃用
    """
    benchmark_result = {"group": [], "member": [], "relation": [], "time": 0}

    def __del__(self):
        print("benchmark resutl:", len(self.benchmark_result["member"]))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"hello": "world"}).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length"))
        req_data = json.loads(self.rfile.read(length))

    def do_PUT(self):
        length = int(self.headers.get("Content-Length"))
        req_data = json.loads(self.rfile.read(length))
        key_id = self.path.split("/")[-1]
        if self.path.find("/groups/") >= 0:
            # print(req_data)
            if req_data["type"] == "MODIFIED" and req_data["object"]["status"]["result"]["status"] == "Ready":
                self.benchmark_result["group"].append(1)  # 原子操作 防止数据不一致
        elif self.path.find("/members/") >= 0:
            # print(req_data)
            if req_data["type"] == "MODIFIED" and req_data["object"]["status"]["result"]["status"] == "Ready":
                self.benchmark_result["member"].append(1)
        elif self.path.find("/memberrelations/") >= 0:
            # print(req_data)
            if req_data["type"] == "MODIFIED" and req_data["object"]["status"]["result"]["status"] == "Ready":
                self.benchmark_result["relation"].append(1)
        else:
            print("some other request: ", req_data)

    def return_success(self):
        self.send_response(200)
        self.wfile.write('{"code": "Success"}')


def notify_init():
    host = ('localhost', int(config["SelfAddr"].split(":")[1]))
    server = HTTPServer(host, Notify)
    print("Notify server listening at ", host[1])

    def handler(sig, frame):
        server.server_close()

    signal.signal(signal.SIGINT, handler)
    server.serve_forever()


def web_server(res, config):
    # group = Manager().list()
    # member = Manager().list()
    # relation = Manager().list()
    group = []
    member = []
    relation = []
    print("Web server started Listen at ", int(config["SelfAddr"].split(":")[-1]))
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(("", int(config["SelfAddr"].split(":")[-1])))
    tcp_server.listen(8096)
    # tcp_server.setblocking(False)
    tcp_server.settimeout(1)

    def handler(sig, frame):
        print("sig handler get")
        res["group"] = len(group)
        res["member"] = len(member)
        res["relation"] = len(relation)
        tcp_server.close()
        exit()
    signal.signal(signal.SIGINT, handler)
    while True:
        try:
            cli_socket, cli_addr = tcp_server.accept()
            p = Thread(target=do_request, args=(cli_socket, group, member, relation), daemon=False)
            p.start()
        except Exception as e:
            pass


def do_request(sock, group, member, relation):
    try:
        recv_data = sock.recv(1024).decode("utf-8").splitlines()
        req_data = json.loads(recv_data[-1])
    except Exception as e:
        print(str(e))
        print("Bad request abort:", recv_data)
        sock.close()
        return
    if recv_data[0].split(" ")[0] == "PUT":
        if recv_data[0].find("/groups/") >= 0:
            if req_data["type"] == "MODIFIED" and req_data["object"]["status"]["result"]["status"] == "Ready":
                group.append(1)
        elif recv_data[0].find("/members/") >= 0:
            if req_data["type"] == "MODIFIED" and req_data["object"]["status"]["result"]["status"] == "Ready":
                member.append(1)
        elif recv_data[0].find("/memberrelations/") >= 0:
            if req_data["type"] == "MODIFIED" and req_data["object"]["status"]["result"]["status"] == "Ready":
                relation.append(1)
        else:
            print("unknow request")
    response_headers = "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
    sock.send(response_headers.encode("utf-8"))
    sock.close()


def show_result(group, member, relation, benchmark_result):
    t = time.time() - benchmark_result["time"]
    print("""Benchmark result:
    TimeCost     {}   seconds
    Group        total:  {}  success: {}
    Member       total:  {}  success: {}
    Relation     total:  {}  success: {}
""".format(t, len(group), benchmark_result["group"], len(member),
           benchmark_result["member"], len(relation), benchmark_result["relation"]))


def get_url_data_encode(datadict) -> bytes:
    return urllib.parse.urlencode(datadict).encode("utf-8")


def get_core_http_addr(s="") -> str:
    return "http://" + config["MediaCoreAddr"] + "/mediacore/v1/" + s


def get_call_back_url(s) -> str:
    return "http://" + config["SelfAddr"] + "/" + s


def create_group(d) -> str:
    """创建组
    req = urllib.request.Request(get_core_http_addr("groups"), headers=DEFAULT_HTTP_HEADER, method="GET")
    urllib.parse.urlencode(data).encode("utf-8")
    返回值 列举
    {"code":"Success","object":{"metadata":{"name":"group_efa8eee5-3e38-476c-b0b3-0dc475b8497a"},
    "spec":{"groupID":"group_efa8eee5-3e38-476c-b0b3-0dc475b8497a","ctx":"111111111","member_retry_times":3,"member_relation_policy":"OneSrcReady"},
    "status":{"result":{"status":"Processing"},
    "accessURL":"/apis/mediacore.mediaschedule.io/v1/namespaces/media-schedule-system/mediagroups/group_efa8eee5-3e38-476c-b0b3-0dc475b8497a"}}}
    """
    # 参数枚举类型
    # member_relation_policy enum  [ OneSrcReady, AllSrcReady ]
    global group
    data = {
        "callBack_url": get_call_back_url("group"),
        "spec": d
    }
    try:
        req = urllib.request.Request(url=get_core_http_addr("groups"), data=bytes(json.dumps(data), "utf8"),
                                     headers=DEFAULT_HTTP_HEADER, method="POST")
        rsp = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    except Exception as e:
        print(str(e))
        return ""
    if rsp["code"] != "Success":
        print("Create group err", str(rsp))
        return ""
    return rsp["object"]["spec"]["groupID"]


def benchmark_create_group(pid, task_num):
    print("Process ", pid, " start work  task num ", task_num)
    i = 0
    while True:
        if 0 < task_num <= i:
            break
        d = {
            "ctx": str(uuid.uuid4()),
            "member_retry_times": 3,
            "member_relation_policy": "OneSrcReady"
        }
        create_group(d)
        i += 1


def create_member(d) -> str:
    """创建成员 编码设备填写编码能力，  解码设备填写解码能力
    返回值举例
    {'code': 'Success', 'object': {'metadata': {'name': 'member_6e4081b8-3a30-4adb-a8e7-c5946decd7f9_456'},
    'spec': {'groupID': 'group_efa8eee5-3e38-476c-b0b3-0dc475b8497a', 'resourceID': '456', 'resource_login_nodeID': '123',
    'ability': {'encode_supported': True, 'encode_ability': {'encode_type': 'Video', 'channel': 'channel-0'},
    'decode_supported': True, 'decode_ability': {'decode_type': 'Video', 'channel': 'channel-0', 'transport_type': 'unicast'}},
    'passive': True, 'retry_times': 5}, 'status': {'result': {'status': 'Processing'}, 'ability': {}}}}
    """
    # 参数枚举类型
    # encode_type | decode_type enum [Default  Audio  Video  AVBoth]
    # streamType enum [Default  Main  Sub]
    # transport_type enum [unicast  multicast]
    # d = {
    #     "groupID": "group_efa8eee5-3e38-476c-b0b3-0dc475b8497a",
    #     "resourceID": "456",
    #     "resource_login_nodeID": "",
    #     "ability": {
    #         "encode_supported": True,
    #         "encode_ability": {
    #             "encode_type": "AVBoth",
    #             "channel": "channel-0",
    #             "streamType": "Default"
    #         },
    #         "decode_supported": True,
    #         "decode_ability": {
    #             "decode_type": "AVBoth",
    #             "channel": "channel-0",
    #             "transport_type": "unicast"
    #         }
    #     },
    #     "passive": True,
    #     "retry_times": 5
    # }
    data = {
        "callBack_url": get_call_back_url("members"),
        "spec": d
    }
    req = urllib.request.Request(url=get_core_http_addr("members"), data=bytes(json.dumps(data), "utf8"),
                                 headers=DEFAULT_HTTP_HEADER, method="POST")
    rsp = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    if rsp["code"] != "Success":
        print("Create member err:", str(rsp))
        return ""
    return rsp["object"]["metadata"]["name"]


def benchmark_create_member(pid, task_num, gid, member):
    print("Process ", pid, " start work  task num ", task_num)
    i = 0
    while True:
        if 0 < task_num <= i:
            break
        d = {
            "groupID": gid,
            "resourceID": str(uuid.uuid4()),
            "resource_login_nodeID": "",
            "ability": {
                "encode_supported": True,
                "encode_ability": {
                    "encode_type": "AVBoth",
                    "channel": "channel-0",
                    "streamType": "Default"
                },
                # "decode_supported": True,
                # "decode_ability": {
                #     "decode_type": "AVBoth",
                #     "channel": "channel-0",
                #     "transport_type": "unicast"
                # }
            },
            "passive": True,
            "retry_times": 5
        }
        mid = create_member(d)
        member[mid] = ""
        i += 1


def create_relation(d) -> str:
    # 参数枚举类型
    # mode enum [ Seprated  Split]
    # srcs_policy enum [ OneSrcReady  AllSrcReady]
    d = {
        "groupID": "groupid",
        "dst_memberID": "mamberID_ooooooooo",
        "video_src": {
            "mode": "Split",
            "srcIDs": ["memberID_xxxxxxx"],
            "max_splitter": 0,
            "layout": {
                "regions": [{"srcID": "11", "left": "123", "top": "111", "relative_size": "666"}]
            }
        },
        "audio_src": {
            "mode": "Split",
            "srcIDs": ["memberID_xxxxxxx"],
            "max_mixer": 0
        },
        "srcs_policy": "OneSrcReady"
    }
    data = {
        "callBack_url": get_call_back_url("memberrelations"),
        "spec": d
    }
    req = urllib.request.Request(url=get_core_http_addr("memberrelations"), data=bytes(json.dumps(data), "utf8"),
                                 headers=DEFAULT_HTTP_HEADER, method="POST")
    rsp = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    if rsp["code"] != "Success":
        print("Create member err:", str(rsp))
        return ""
    return rsp["object"]["metadata"]["name"]


def benchmark_create_relation(pid, task_num, gid, relation):
    print("Process ", pid, " start work  task num ", task_num)
    i = 0
    while True:
        if 0 < task_num <= i:
            break
        d = {
            "groupID": gid,
            "dst_memberID": "mamberID_ooooooooo",
            "video_src": {
                "mode": "Split",
                "srcIDs": ["memberID_xxxxxxx"],
                "max_splitter": 0,
                "layout": {
                    "regions": [{"srcID": "11", "left": "123", "top": "111", "relative_size": "666"}]
                }
            },
            "audio_src": {
                "mode": "Split",
                "srcIDs": ["memberID_xxxxxxx"],
                "max_mixer": 0
            },
            "srcs_policy": "OneSrcReady"
        }
        mid = create_relation(d)
        relation[mid] = ""
        i += 1


def generate_resource_config(num) -> bool:
    """
    生成相应的资源数据
    用于上线
    """
    global config
    path = os.path.dirname(sys.path[0])
    default_path = path + "/instance/resource/"
    data = "SEQUENTIAL"
    for i in range(num):
        account = config["SipAccountStart"] + i
        data += "\n{};[authentication username={} password=123456];".format(account, account)
    try:
        f = open(default_path + "auth_encode.csv", mode='w')
        f.write(data)
        f.close()
    except Exception as e:
        return False
    print(" Ok  add auth_encode file :", default_path + "auth_encode.csv")
    data = "SEQUENTIAL"
    for i in range(num):
        account = config["SipAccountStart"] + num + i
        data += "\n{};[authentication username={} password=123456];".format(account, account)
    try:
        f = open(default_path + "auth_decode.csv", mode='w')
        f.write(data)
        f.close()
    except Exception as e:
        return False
    print(" OK  add auth_decode file :", default_path + "auth_decode.csv")
    return True


def clean_all():
    """
    清除所有的组， 成员， 成员关系
    """
    req = urllib.request.Request(url=get_core_http_addr("groups"),
                                 headers=DEFAULT_HTTP_HEADER, method="GET")
    rsp = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    if rsp["code"] != "Success":
        print("ERROR  can`t get group list , Please try again later")
        return
    if "items" not in rsp.keys():
        print("Nothing to do")
        print("Finish!")
        return
    for item in rsp["items"]:
        req = urllib.request.Request(url=get_core_http_addr("members/group/" + item["metadata"]["name"]),
                                     headers=DEFAULT_HTTP_HEADER, method="DELETE")
        rsp = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        if rsp["code"] != "Success":
            print("ERROR  can`t get group list , Please try again later")
            return
        req = urllib.request.Request(url=get_core_http_addr("memberrelations/group/" + item["metadata"]["name"]),
                                     headers=DEFAULT_HTTP_HEADER, method="DELETE")
        rsp = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        if rsp["code"] != "Success":
            print("ERROR  can`t get group list , Please try again later")
            return
        print("Clean : ", item["metadata"]["name"], " `s  member and relation    Success")
    req = urllib.request.Request(url=get_core_http_addr("groups"),
                                 headers=DEFAULT_HTTP_HEADER, method="DELETE")
    rsp = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    print("Clean :  groups  ", rsp["code"])
    print("Finish!")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(CMD)
        exit(0)
    else:
        if sys.argv[1] not in ["init", "start", "clean"]:
            print(CMD)
            exit(0)
    if sys.argv[1] == "init":
        try:
            num = int(sys.argv[2])
        except Exception as e:
            print("Error Option : need an int param to generate")
            print(CMD)
            exit(0)
        print("Start to generate test resource data for benchmark")
        if generate_resource_config(num):
            print("Finish!!")
        else:
            print("Error!!")
        exit(0)
    elif sys.argv[1] == "clean":
        print("Start to clean all group member relations data")
        clean_all()
        exit(0)
    elif sys.argv[1] == "start":
        try:
            process_num = int(sys.argv[2])
            task_num = int(sys.argv[3])
        except Exception as e:
            print("Error Option : need tow int param to start benchmark  ", str(e))
            print(CMD)
            exit(0)
        group = Manager().dict()
        member = Manager().dict()
        relation = Manager().dict()
        benchmark_result = Manager().dict({"group": 0, "member": 0, "relation": 0, "time": time.time()})
        # web = Process(target=notify_init, args=(group, member, relation))
        # web.start()
        web = Process(target=web_server, args=(benchmark_result, config))
        web.start()
        # w = web_server(benchmark_result)

        def interrupt(sig, frame):
            print("Keyboard interrupt signal")
            web.kill()
            show_result(group, member, relation, benchmark_result)
            exit(0)
        signal.signal(signal.SIGINT, interrupt)
        time.sleep(1)  # 等待回调web server启动
        gid = create_group({
                "ctx": str(uuid.uuid4()),
                "member_retry_times": 3,
                "member_relation_policy": "OneSrcReady"
            })
        # python .\mocker\benchmark\benchmark.py start 10 2
        p_list = []
        for i in range(int(sys.argv[2])):
            go = Process(target=benchmark_create_member, args=(i, task_num, gid, member))
            go.start()
            p_list.append(go)
        for p in p_list:
            p.join()
        print("all request has been send")
        web.join()
        show_result(group, member, relation, benchmark_result)

