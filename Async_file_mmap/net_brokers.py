import asyncio,threading,subprocess, mmap 
import logging, hashlib, argparse
import signal, sys, os, time
import inotify.adapters, inotify.constants
from elasticsearch._async.client import AsyncElasticsearch

# Variables
global file_path, fichier_init
dossier= "ready/"
watch_dir = "cap_json/"
stop_jq = 0
event_trap = threading.Event()
file_list = []
hash_list = []

client = AsyncElasticsearch(
    "https://10.190.100.210:9200/",
    ca_certs="elk_ca.crt",
    api_key="cVBmOVRJOEI1Rk1MRmJudzI4LUk6UEpnZFVBY0pUS3FTeGl4aFBHS0pRZw==")

# Parser argument
arg_p = argparse.ArgumentParser(prog="tinda",description="Network Packer Broker, Get packets visibility",epilog="Sometimes in Network Security, We need to see")
arg_p.add_argument("-t", "--test", action="store_true", help="try connection to elastic search)")
args = arg_p.parse_args()
if args.test:
    print(client.info())
    sys.exit(0)

# Inotify part
i = inotify.adapters.Inotify()
i.add_watch(watch_dir, inotify.constants.IN_CLOSE_WRITE)

# Logging 
logging.basicConfig(
    level=logging.INFO, filename="/var/log/async_elk.log",filemode="a",
    format="%(asctime)s %(levelname)s msg:%(message)s")

# Functions to handle Linux signals 
def handle_signal(signum, frame):
    event_trap.set()
    t1.join()
    t2.join()
    i.remove_watch(watch_dir)
    logging.warning(f"Process end with signal: {signal.Signals(signum).name} ")
    time.sleep(1)
    sys.exit(0)

# Signal Trap
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

# Function to manage repertory events
def events_looping():
    try:
        logging.info(" Events loop start succesfully")
        for event in i.event_gen():
            if event is not None:
               (header, type_names, watch_path, filename) = event
               if 'IN_CLOSE_WRITE' in type_names:
                   if os.path.getsize(os.path.join(dossier, filename)) > 10:
                       file_list.append(filename)
            if event_trap.is_set():
               logging.info("Events loop stop succesfully")
               break
    except Exception as lo:
        logging.warning(f"Events loop failed: {str(lo)}")

# Functions for deduplication 
def dup_packets(raw_packets, cont, hash_list):
    for i, h_cap in enumerate(raw_packets):
        cap_hash = hashlib.md5(h_cap.encode("utf-8")).hexdigest()
        if cap_hash not in hash_list[-100:]:
            hash_list.append(cap_hash) 
        else:
            if i==0:
                cont.pop(i+1)
                cont.pop(i)
            else:
                cont.pop(i*2)
                cont.pop((i*2)-1)
    return "\n".join(cont)

# Functions allowing sending to elasticsearch (Phase 2)
async def to_elk(client, ft_packets, fichier_init):
    try:
        logging.info(f"File {fichier_init} start ")
        response = await client.bulk(body=ft_packets)
        if str(response["errors"]) == "False":
            file_list.remove(f"{fichier_init}")
            os.remove(os.path.join(watch_dir, fichier_init))
            os.remove(os.path.join(dossier, fichier_init))
        else:
            logging.error(f"{fichier_init} Failed in Elasticsearch")
    except Exception as e:
        logging.error(f"Error sending data to elasticsearch: {str(e)}")

# Preprocessing functions (data cleaning), at end data is stored in dossier repertory (Phase 1) 
async def process_file(file_path, fichier_init):
        try:
            jq = await asyncio.create_subprocess_exec("./script_async.sh",f"{fichier_init}", stdout=subprocess.PIPE)
            output, error = await jq.communicate()
            if error:
                logging.warning(f" {fichier_init} jq filter failed")
                stop_jq = stop_jq + 1
                if stop_jq == 6:
                    logging.error(f" Many files failed in jq filter")
                    sys.exit(0)
            else:
                with open(file_path, "r") as fi:
                    m_objet= mmap.mmap(fi.fileno(),length=0,access=mmap.ACCESS_READ,offset=0)
                    cont = m_objet.read().decode('utf-8').splitlines()
                    raw_packets = cont[1::2]
                    ft_packets=dup_packets(raw_packets, cont, hash_list)
                    await to_elk(client, ft_packets, fichier_init)
                    m_objet.close()
        except Exception as lo:
            logging.error(f" Error with process_file: {str(lo)}")

# Main function: code leader 
async def main():
    while True:
        file_unit = file_list
        if len(file_unit) >= 5:
            tasks = []
            for untel in file_unit[:5]:
                file_path = os.path.join(dossier, untel)
                fichier_init = untel
                task = asyncio.create_task(process_file(file_path,fichier_init))
                tasks.append(task)
            await asyncio.gather(*tasks)
            if len(hash_list) > 1500:
                hash_list.clear()
        if event_trap.is_set():
           logging.info(" Async loop stop succesfully")
           await client.close()
           break
        time.sleep(1)

# Launch Functions allowing allowing to put the async main() function in a thread
def real_main(cor):
    asyncio.run(cor)


# First we launch Events loop after real_main --> async main()
t1 = threading.Thread(target=events_looping)
t1.start()
t2 = threading.Thread(target=real_main, args=(main(),))
t2.start()

# Waiting Threading events
event_trap.wait()


# sudo mount -t tmpfs tmpfs /etc//npb/cap_json/ -o size=200M (No important)
# sudo mount -t tmpfs tmpfs /etc//npb/ready/ -o size=200M ()
# sudo mount -t tmpfs tmpfs /tmp/ -o size=200M (Mettre une fonction de verification si /tmp existe deja dans tmpfs )
# ip -s link ls dev eth0
# sudo ethtool -g eth0  ( donnes les stats de l'interface eth0 )
# Get-NetAdapter
# Get-NetAdapterAdvancedProperty -Name "Ethernet"
# Set-NetAdapterAdvancedProperty -Name "Ethernet" -DisplayName "Receive Buffers" -DisplayValue 512