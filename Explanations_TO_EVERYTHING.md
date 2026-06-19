====================RABBITMQ_PUBLISHER================================
Rabbitmq_publisher : So we use a TCP connection to RabbitMQ broker. Create channels which don not create a new TCP connection. THE RABIITMQ FILE CONTAIN THE ETHODS FOR THE SERVICE FILES (EBAY AND TCG). EVERYHTING INITILAIZED IN RABBITMQ IS CALLED IN MAIN(THE ORCHESTRATOR AND ONCE MAIN CREATES A RABBITMQ PUBLISHER IT THEN PASSES INTO EBAY SERVICES AND TCG SERVICES IN THEIR RESPECTED INIT FUNCTIONS. FROM THERE INSIDE THOSE SERVICE FILES THEY CALL METHODS FROM rabbitmqpublisher SUCH AS **await self.publisher.publish("listings", payload)** USED FOR SINGLTETON USE THATS WHY GLOBAL IS CALLED **global publisher, ebay_svc, tcg_svc** AND HERE PUBLISHER IS INITIALIZED **publisher = RabbitMQPublisher(rabbitmq_url)** THEN PASSED TO THE SERVICE LAYER **ebay_svc = EbayService(repo=EbayRepo(), publisher=publisher) tcg_svc = TCGService(repo=TCGRepo(), publisher=publisher)**.


queue_report.py: SCRIPT TO CHECK IF RABBITMQ IS UP AND RUNNING HEALTHY. FIRST CONNECTS TO RABBITAMQP AND RABBITMGMT WHICH IS A MANAGMENT TOOL TO SEE RABBITMQ DIAGNOSTICS BY LOGGING IN WITH USERNAME AND PASSWORD. CLASS QUEUEREPORTER TAKES IN TWO ARGUMENTS WHIHC ARE CONNECTION URLS. ASYNC DEF CHECK CONNECTION CONNETCS TO AMQP. CHECK QUEUES AMQP TAKES IN THE QUEUE NAME WHCIH IS ONLY listing we only have one queue name and that can be confirmed in TCG AND EBAY SERVCIES WHERE THEY APPENDED A LISTING PAYLOAD CALLED LISTINGS. IT CHECKS FOR EACH QNAME. ALSO aio_pika talks to RabbitMq and httpx handles the HTTP requests for the Mnagment Rabbitmq. SO FIRST IT OPENS A CONNECTION THEN A CHANNEL IT ITERATES THROUGH EACH QUEUE NAME IF EXISTS BY using **channel.declare_queue(passive =True)** which means dont touch it just inspect.  the **queue.declarations_result.message_count** checks how many messages are inside the 'listing' queue. The **declaration_result.consumer_count** checks how many messages are sitting in the listings queue. Inside it also chceks if that specific queue names exists if Not rabbitmq kills the channel and onto the next queue and once outer loop existed returns error if couldnt expect queues. The CHECK_MGMT_STATS it first opens a HTTP client . Then hits the the rabbitmq web api  using client.get . Initialzie data to grab all json and then using data.get for the paremeter queue totals and parse the JSN to find the total message count across eveyr queue on the server not just one named listing. Then finally main creates an insnace of the QUEUEReporter and runs the functions inside using await. EVERY PYTHON FILE WILL ALWAYS BE MAIN ITS JUST HOW ETHYRE PORGRAMMED SO IF NAME WILL ALWAYS EQUAL MAIN. **Asyncio.run(main())** means stars the asynchronous event loop to power all await commands

===================== GITHUB ========================
git init: initilaize git
git remote add origin https:// link: add git repo to the remote
git remote: see all rmeote
git config --global user.name "issa402": must do this when adding repo and pushing code
git config --global user.email "is.jimenezinzone@gmail.com
git config --list 
git reflog: shows commits history 
git reset --soft HEAD@{1}: means go back one
git update-ref -d HEAD: deletes the HEAD pointer entirely but files stay exactly where they are but GIT forgets the commit ever existsed.
git rm -r --cached: removes everything it was tracking but doesnt delete the file





=================GITHUB ACTIONS =================================
ci.yml: Always start with "on" and "push" means to the specific branch 
so like main or branch and "pull_requests" so to run the workflow automatically when a pull requests is opened against main or master. "workflow_dispatch" Allows to manually trigger the workflow from the github actions tab. The "jobs" defines the jobs to be executed. "healthcheck" is the name of the specific job. "runs-on" is the specific virtual machine it runs on. "services" defines the docker containers needed for the job. So basically like a config . "steps" is a list of tasks to execute "name is the labels of steps and "uses" is the built in Github action to clone the repository code onto the runner. inside the name labels the step. "uses" uses an action to install Go. "with " is specific to that Go version. "name" and "run: |" starts a multinline bash script. 




===================LINUX (SYS ADMIN) ===================================
sudo ss -tulpn : ALLOWS TO SEE ALL PROCESS AND OPEN PORTS AND THE NAME OF THOSE
pgrep -a "redis": Finds the process ID and shows the full command line
systemctl list-units --type=service --state running: Shows all services and if theyre loaded , active and description
journalctl -u cron.service --since "30 minutes ago": This shows shows the logs from the last 30 minutes
nc -vz localhost 3001: returns connections to that host and succeded or failed.
df -h: Shows how much space in ram and disk 
grep -rn "threhold": the "r" stands for recursive check, the "n" stands for number lined
curl -G http://localhost:3100/loki/api/v1/labels: shows status and data which are containers
lsmod: List all currenlty loaded modules
modinfo modulename: Shows info about specifci module such as author description and params
modprobe: is the standard tool to loading and unloading modules
To Find a directory(Case Insensitive): find . -type d -iname "*everything*" the (-i means case insensitive) and type -d means (directory)
To Find a file: find . -type f -iname "*everything*.md" 
To Switch user: su - labuser
To see users: ls/home
To Give user sudo permissions: sudo usermod -aG sudo labuser - usermod is the system command to chage an exisiting use's setting and -a means append which means add the user to a new group and -G means groups so whatever is after that -aG which is sudo means were adding it to sudo
sudo ss -tulpn : to see PID
kill PID: to get rid of that service from that port
ls -lh ~/.local/share/Trash/files: sees files in trash
du -sh ~/.local/share/Trash/: How much space is in the Trash folder    
rm -rf ~/.local/share/Trash/files/*: remove files in trash
sudo find / -type f \( -name "*.vdi" -o -name "*.vmdk" -o -name "*.qcow2" -o -name "*.vhdx" \) 2>/dev/null: "find /" means the starting point so at the very top of the hard drive(root) searching every subfolder, "-type f means to only look for files "\( -name "*.vdi" -o -name "*.vmdk" -o -name "*.qcow2" -o -name "*.vhdx" \) the "\(" meansdont touch the parenthesis pass them directly to find command and we end it with "\)" for a space warning, "-o" means or , "2>/dev/null" means 2 means error , > means redirect that output, /dev/null is the linux black hole
ps aux --sort=-%cpu | head -n 11: see the top 11 processes using cpu 
pip show pyyaml: check if you have that version
uname -a: It shows kernal name and ubuntue server, shows kernel releae version , shows architecture and operating system name
cat /etc/os-release: shows specific details on Linux distrubtuin like version id and supprot links
uptime: current system time, shows duration since last boot, shows number of users currenlty logged in , and load average means system cpu usage over the last 1,5, and 15 minutes
id: shows current user
ls -la : gets you drwxr-x--- 72 iscjmz iscjmz  4096 Apr 26 13:16  . so the "d" means directory and the rwx means all permisiions read write excecute, r-x means the group can read it , and the --- means no randoms can open it.
chmod 755 seed_cards.py : mean change permissions (read, write, execute) r(Read) = 4, w(Write) = 2, x(Execute) = 1
sudo chown john:developers report.txt: This makes John the owner of the file and sets the group to developers
sudo -l: means it iwll shosw the commands that all user and groups can run 
journalctl -xe: looks at the systemd journal which is centralized digitial databse of all systems logs (-x) adds explantory help text to error messages to help you fix, (-e) immediately jumps to the very end of the lg so you see the most recent events first
tail -f /var/log/syslog: (-f) means follows the the new lines to your screen as they happen in real time, is the specific file path where linux store global messages so from all plugins like power
mount -t vfat /dev/sdc /mnt/flash :Linux treats everyhting like filesystems so when u plug in a usb you must create a file system and mount the usb so like 
###### NGINX #####
systemctl status nginx: means check if nginx is running
sudo shutdown now: in a virtual machine this shutdowns the virtual machine
ls -ld /var/www: lets us see perms and groups 
ls -R /var/www/html: lets us see the path with all the files inside of the path
cat /var/log/nginx/access.log: see who accessed
sudo journalctl -xe: Shows everything
sudo cat /var/log/auth.log: shows login and sudo and ssh attempts and permission issues
sudo nginx -t:shows if nginx is running and healthly
sudo systemctl reload nginx: reloads nginx
sudo nano /etc/nginx/sites-available/deafult: Shows location and server configurations
In the file theres server and location; to turn it in a reverse proxy go to location the "/" means for any requests nginx forwards it to the backend app on port 500, the Host header: preserves the original host header, and the X-Real-IP: passes the clients IP to the backend(so logs show real IP not nginxs) so goes to (Browser -> 8080(host) -> 80(VM, NGINX) -> 5000(backend app),
sudo nginx -t: parse all ninx configs checks for any errors
sudo systemctl reload nginx: reloads nginx with the new config file
so from host: http://127.0.0.1:8080
so sudo mkdir /etc/nginx/ssl : to create the folder for SSL assetsto keep certs and keys
sudo openssl genrsa -out server.key 2048:creates an openssl to generate a 2048 bit RSA private key and saves it as a server.key
sudo openssl req -new -x509 -key server.key -out server.crt -days 365: req -new: creates a new certificate request, -x509: output a self signed certificate instead of a CSR, and -key server.key: sign it with your private key, -out server.crt: write the certifcate here, -days 365: valid for 1 year, so the result is server.crt= public certificate(contains public key +metadata = signature)
nginx ssl configuration: to listen on 443 with SSL to use both cert + key but must edit the site-availabe/defaults add the new port 443 and certifcate key 

==================DOCKER =================================================
docker compose up -d : is to run everything in the docker-compose.yml 
docker inspect {container_name}: inspect everythign in the contianer for image to network everything
We made services talk to local host only by doing this :  ports: - "127.0.0.1:5432:5432" 
Use sudo ss -tulpn to see the services running You will now see: cp    LISTEN  0        4096           127.0.0.1:5672           0.0.0.0:* (Means who am i talking to )     users:(("docker-proxy",pid=1665170,fd=7))  
In the bottom of the docker file where it says volumes the pgdata has to always be pokevend_pgdata since that has our original data. 
docker compose down stops every container(it doesnt delete any data)
This line shows us the size of the volume du means disk usage and -s means summary, and h means human readable : sudo du -sh /var/lib/docker/volumes/{pokemon_pgdata,pokevend_pgdata,prediction-engine_postgres_data}
Eg.47M	/var/lib/docker/volumes/pokemon_pgdata ..... 64M	/var/lib/docker/volumes/pokevend_pgdata
This line shows us permissiosn and dates -l stands for long format which shows permissions, -d stands for directory : sudo ls -ld /var/lib/docker/volumes/{pokemon_pgdata,pokevend_pgdata}/_data
Eg.drwx------ 19 70 70 4096 Apr 13 10:54 /var/lib/docker/volumes/pokemon_pgdata/_data
drwx------ 19 70 70 4096 Apr 13 10:54 /var/lib/docker/volumes/pokevend_pgdata/_data
This line chekcs how much a service is being used : docker exec -it pokemontool_redis redis-cli info stats | grep total_commands_processed
To see where specific things are use: grep -r "Redis" or grep -r "redis" services/api-consumer
This line checks docker lines: docker compose logs --tail=10
docker compose config --services: Shows all services started by docker
docker compose stop grafana: stops the service
docker compose up -d grafana: starts the service wihtout watch mode
docker compose up grafana: starts the services with watch mode
docker network ls: The Name means the Networks eg.bridge(standard playground. No specified network), host(container shares laptops IP), none(isolation), pokemon_default(created by docker compose and it becomes the User Definded Bridge WHICH ALLOWS THE CONTAINERS IN THESE NETWORKS TO TALK TO EACH OTHER) Example: If your pokemon_default network has a web container and a db container, the web app can just connect to http://db:5432 instead of trying to guess an IP address.
docker network inspect pokemon_default: you see all containers
When running docker compose it creates the names network based on the directory name
Docker essentially is a mini cloud containing oru services YOU CAN ALSO DEFINE SUBNETS AND GATEWAY NETWORKING
ls -l /var/lib/docker/containers: is the default location on LInux systems where the Docker daemon stores the configuration, logs and state files for eveyr container running
running_id=$(docker ps -q -f"name=^${container_name}$"): -q means quite only output the ID and -f means to filter and -aq means showing all containers even stopped burt only IDs, the "^" means the start of the string, and the "$" at the end means matching the end
GO_PID=$!: means hold the PID of the very last command
docker stats: sees ram and memory of every container
Dockerfile: tells docker how to build an image for your app
After building docker file run "docker build -t backend-app:latest .:  which docker build means build an image from a Dockerfile, -t backend-app:latest means tag/name the image backend-app with tag latest, and the "." builds context = current directory
docker images: to see image ID and Disk usage
docker run --name backend-test -p 5000 backend-app:latest: start a container from an image, --name backend-test: gives the container a name, -p 5000:5000:means host(VM) port 5000 -> container port 5000, backend-app:latest: which image to run
curl http://127.0.0.1:5000: shows container is running and flask is listening on port 5000 inside the container 
docker network create app-net: This creates a virtual layer 2 network inside Docker,so eveyr container that gets attached to it gets its own virtual NIC( Network Interface Card) whihc acts like a private room for its network settings: the veth pair: docker creates a virual ethernet pair which acts like a virtual cable, Eth0: One end of this cable is placed inside the container as a virtual NIC,  Host connection: The other end stays on the host and connects to a virtual switch allowing the container to talk to other containers or the internet)), Internal Ip address: each container is automatically assigned its own private IP address when it starts. Subnets: Docker manage a priavte range of IPs, Dynamic Assignment: These IPs are unique within the network. You dont have to worry about IP conflicts between containers because the Docker daemon manages the allocation for you, Gateway: the virtual bridge itself acts as the default gateway routing traffic between the container and the outside world.)), Automatic DNS resolution: On user defined networks Docker runs an embedded DNS server that allows containers to communicate using names instead of IPs. Service Discovery: When you create a container with a name; Docker alreayd registers that name in the internal DNS, Resolution: other containers on the same network can reach it by simply pinging  mydb. Docker DNS sever resolves that name to the containers current internal IP, Reliability:  Critical because containr IP addresses can change whenever a container is restarted or recreated; names, however usually stay the same)) Contianers talk to each other by name not IPs
docker run -d \ (newline) --name backend \ (newline) --network app-net \ (newline) backend-app:latest: the "-d" means run in background, --name backend means container name becomes backend and --network app-net means attaches it to the private Docker network, So no more port 5000 since backend is now private
docker exec -it backend curl http://127.0.0.1:5000: pings the backend, "docker exec" is the core command which means to run a new command inside an existing container, "-i" means keep the Standard input which allows you to type anything in the container, "-t" allocates a virtual terminal which makes the screen look like a real terminal. Which enables things like color coded text , "backend" name of this ID of the container
Docker container A -> docker bridge -> container B
Path from a containers to the internet looks like:container 172.18.0.2-> docker bridge on host-> laptop 192.168.1.12-> router 192.168.1.1-> internet
##### NGINX & DOCKER ######
mkdir -p ~/nginx-docker: the folder that will hold the nginx reverse proxy config, SSL certs
create the config file (default.conf): which has the server and location, in the proxy pass "backend" isnt an IP its the contianer name (each container gets its own virtual NIC, INTERNAL IP, and DNS name
docker run -d \ (newline) --name nginx \ (newline) --network app-net \ (newline) -p 8080:80 \ (newline) -v $(pwd)/default.conf:/etc/nginx/conf.d/default.conf:ro \ (newline) nginx:stable : --name nginx (gives the container a name so you can refernce it, --network app-net attaches nginx to the same network as your backend container, -p 8080:80 means maps VM port 8080 -> nginx container port 80 so that the host can reach nginx through VirtualBox, -v$(pwd)/default.conf:/etc/nginx/conf.d/default.conf:ro which mounts your custom config into the container. :ro = read only, nginx:stable is the offical nginx image, the container is now your reverse proxy
docker ps -a : see all active and stopped containers
mkdir -p ~/nginx-docker/ssl: "-p" means if exisited dotn create it again , we're creating a folder for our ssl key and crt
openssl genrsa -out server.key 2048: "openssl" this is commandline tool used for generating keys, creating certificate requests, and encrypting data, "genrsa" uses an algorithm to create a Key pair even though the command saves a file called server.key, "-out server.key" means redirects that data into a file , server.key is the filename and 2048 is the key size measured in bits
openssl req -new -x509 -key server.key -out server.crt -days 365: creates the actual ID card, "req -new" tells openssl to create a new certificate requests, "-x509" tells openssl to create a self signed certificate instead of just a request, x.509 is the official international standard format for a public key certifcates (its what browsers look for to verify a sites indentity, "-key server.key": Use the private key I just made to sign this certificate(so creaes a link between the .key and the .crt if thye fail to mathc nginx will fail), -out server.crt : contains the public key and information about your server(unlike the key file the .crt is meant ot be shared to the world", "-days 365" sets the expiration date
In the nginx-docker /default.conf you must add the two servers one for port 80 and for 443 ssl 
docker run -d \ (newline) --name nginx \ --network app-net \ -p 8080:80 \ -p 8443:443 \ -v $(pwd)/default.conf:/etc/nginx/conf.d/default.conf:ro \ -v $(pwd)/ssl:/etc/nginx/ssl:ro \ nginx:stable : "--network app-net" means same network as backend container, "-p 8080:80" means vm port 8080 ngingx HTTP for redirect, -p 8443:443 means vm port 8443 _. Nginx HTTPS, -v default.conf means mount your config into container, -v ssl: mount cert + key into /etc/nginx/ssl
RECAP: FULL PATH IS HOST-> 8080(HTTP) / 8443(HTTPS)->VirtualBox Port forwarding -> VM 8080 /8443 -> Docker Port Mapping ->Nginx Container(HTTP->HTTPS +SSL termination) ->DOCKER NETWORK(app-net) -> backend container(Flask on 5000)
0.0.0.0:8080->80/tcp means on all network interfaces on the host so it means accept all connections, 8080 is the host(vm) port when something inside the vm connects to 127.0.0.1:8080  Docker will forward that traffic into a container and ->80 is the container port which is inside the ngnix container so nginx is listening on port 80 SO ON THE VM listen on port 8080 on all interfcaes and forward that traffic into the containers port 80(TCP)
In docker compose-yml always include : restart: unless-stopped; So that the containers auto start after the VM rebooot and any crash
docker compose down: stops contianers
docker compose up -d --build: Rebuilds backend image and restarts containers with new image
In the dockerfile create adduser and a non root user also change ownership so the user can read the files and switch to the non root user and insdie the docker-compose.yml update it so backend is read only and cap_drop drops all linux capabilities and cap add only allows binding to low ports if needed,must rebuild aftewards 
docker exec -it backend sh: creates a shell inside backend so you can run whoami
ip -br addr: Shows ip addresses with status whether up or down and newtorks





========================== POKEMON PYTHON STACK ==========================
Everything for python is under services/
ONLY IN analytics-engine and api-consumer

######### Promethues.yml ###########
ells Prometheus where to collect metrics. Prometheus does not know your Go app automatically; it repeatedly calls http://server:3001/metrics, reads metric names like pokemon_data_freshness_age_minutes, stores them over time, and adds labels like job="pokemon-server" and instance="server:3001".

=========================== GRAFANA ======================================
For Grafana you must add two other services along side wiht it in the docker compose file.
loki: is the log storage that store all of our docker logs
promtail: is what extracts the logs from loki and sends it to grafana which is the dashboard
{container=~".+"}: Means show me every container that has a name


=========================== BASH SCRIPTS ====================================
-dev-startup.sh:
set -eou pipefail: "-e" means exit immediately if any command returns zero, "u": treeats unset varibales as an error. If no varibale has been assigned its an eror. "o pipefail" : change the return status of a pipeline.
Variables Must Not Be Spaced
SCRIPTS_DIR=$(cd -- "$(dirname -- "$0")" && pwd) the parenthesis insid eexecute first and the "--" means safety check, dirname gets the diretcory naem and the $0 is the last one in the line. 
############ BASH ################
rg -n "errror": looks for lines that have error
rg "Data": Looks for files that have Data
curl -fsS http://localhost:3001/health >/dev/null: "-f" means failed, "s" means silent and "S" means show error
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)": ${BASH_SOURCE[0]} is the script file path.
if docker ps --format '{{.Names}}' | grep -qx "pokemontool_postgres"; then: '{{.Names}}' is the column
while IFS= read -r line;: "IFS" means It tells Bash which characters to use when splitting a line into words. The "-r" means / dont get interperted as escape characters, "line" is simply a variable name
done < file.txt: redirectts to file.txt
awk '{print $1}' logs/2026-04-05T01:34:41/go.log | uniq -c: awk print $1 means first column and uniq -c means the count of each unique one
man systemctl: shows all the keywords with explanations
systemctl -- (press tab twice): Shows all the keywords
grep -iE "error|fatal|panic" : the "i" means incase insensitive and the "E" means extended regex which allows us to use more than one "|"
today="$(date +%F)": get todays date
df -h | awk '{print $1, $2}' | column -t: "column -t" make it nicer and readable
============================ POSTGRES ==========================================
.env: All Configuration Requiremnts(such as Database Host, User, Password Etc) 
config.go: grabs all config requirements and puts it into a function Load
db.go: uses config pointer to then start connection
schema folder: has all sql migrations
so when I run docker compose up first time it checks volumes for all schema migrations files and run all of those
-----001_init.sql:
Line create extenson if not exists "pgcrypto" : is indepotnet and pgcrypto gives cryptographic powers inside SQL queries and it allows you to protect sensitive data without having ot move it back and forth betwee the datase and application code


============================ Firewall/Networking =================================
sudo ufw allow 8080, sudo ufw allow 8443, sudo ufw enable:Only allows those por>
sudo ufw status verbose: shows all ports and which are allowed
ip a: Shows eveyr network interface on the machine . It will show in numbered order and "lo" means localhost which means the machines talks to itself when open like [http://](http://127.0.0.1:8123) and http://localhost:3001. "enp2s0f0" is the wired ethernet port and <NO-CARRIER,... state DOWN> means no ethernet cable is plugge in. "wlp3so" is the wifi and the addres which in our case is 192.168.1.12 which means another device on the home wifi could reach the machine at that IP. docker0 and br-60dbffe54fcd      172.18.0.1/16 and br-e6fc2f29c6d4      172.19.0.1/16 etc are all docker bridge networks. These are so that containers can talk to each other. The 172.xxx are private addresses Docker network inside the laptop not wifi ip. When it says No carrier state down it means no active contianers are attached to that docker network right now. So in docker compose it says ports: "127.0.0.1:5432:5432" that means postgres is only reachble from your own laptop. but when it says ports: "3001:3001" it means it may be reachable from your laptop and maybe your LAN at http://192.168.1.12:3001 like how we saw in the wlp3so
hostname -I: Shows Ip addresses assigned to machine
ip route: your laptop -> WIFi card -> router-> internet default via 192.168.1.1 dev wlp3s0 proto dhcp src 192.168.1.12 metric 600 . 192.168.1.1: sends traffic to router, dev wlp3so: uses wifi interfaces, protodhcp: means the route was assigned automatically by your router via DHCP, and src 192.168.1.12: Your laptop’s IP address. and metric 600: The "cost" of the route. Lower numbers are higher priority. 600 is typical for Wi-Fi. 172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown.  172.17.0.0/16: A virtual network for Docker containers. dev docker0: The virtual bridge interface Docker uses. scope link: This network is directly reachable on this interface (no router needed). linkdown: No containers are currently running on this specific bridge.
ping -c 4 192.168.1.1: 64 bytes: The size of the test packet. icmp_seq=1: The first packet of the batch.ttl=64: "Time to Live." It means the packet can jump through 64 routers before dying. Since it's 64, it proves the router is literally one hop away. time=21.6 ms: How long the round trip took. Under 30ms on Wi-Fi is good. ping -c 4 google.com: rtt min/avg/max/mdev = 12.104/12.759/13.924/0.692 ms min: Your fastest response.avg: The average speed (14ms is very fast).max: Your slowest response.mdev: "Mean Deviation." This shows how stable the connection is. 0.295 is extremely low, meaning your Wi-Fi is rock solid with no "jitter."
ip -br addr: Shows ip addresses with status whether up or down and newtorks
dig +short google.com: Shows what Ip a DNS name resolves to 
nc -vz localhost 3001: Checks TCP connection
getent hosts github.com: see ip address
dig github.com: see all DNS





=========================== FUTURE STANDARD OBJECTIVES ============================
-seamless operation of infra 
-support and operations of platforms
-improve effciency and risk profile 
-document solutions and workflows
-investigate system events and defects
-scripting/programming to automate analysis

Ways to think:
v1:inventory + runtime report
v2:severity levels and nonzero exit code on critical findings
v3:markdown output for docs
v4:compare report snapshots over time for drift
v5:dependency graph visualization

###### pokemon_runtime_dependency_auditor.py ##################
- What services exist?
- Which ones are running?
- Which ones are healthy?
- Which ports are exposed on the host?
- Which services depend on other services?
- What is the blast radius if one service fails?
- What basic risks should an infra engineer notice immediately?

**Left Of Migrations File
Script if when we run docker compus up -v and if created at in alerts isn tin todays date flag


===================================== GO Backend =========================
ALWAYS build from lowest dependency to highest:

  Infrastructure (config, DB connection)
       ↓
  Domain Types (models)
       ↓
  Data Layer (store/repository interfaces + SQL)
       ↓
  Business Logic (services)
       ↓
  HTTP Layer (handlers, middleware)
       ↓
  URL Mapping (routes)
       ↓
  Background Jobs (worker)
       ↓
  Wiring (main.go — always LAST)

######### Config.py ######
All application configuration grabs from env using a struct field for orginzation
JWT is used forsigning so it combines both the users data with the JWTSecret to create a unique signature and for verification when the user comes back with that token the server uses the same JWTSecret to recalculate the signature . if they mathc the server know the data wasnt changed by a hacker.
We create getEnv since there will be an error if w euse just getenv since it only checks for one value

####### Healthhandler.go ##########
defines the Pokemon health and freshness HTTP behavior. It checks whether Postgres/Redis are reachable, checks whether important business tables have recent timestamp data, turns those ages into fresh, warning, critical, or no_data, returns JSON for humans at /api/health/freshness, and prints Prometheus metrics at /metrics.

=========================== CODEX DEBUG ====================================
headroom: A user-global context compression/proxy tool for AI coding agents. In this repo it was installed at `~/.local/bin/headroom` and initialized with `headroom init --global --memory codex`. This helps future Codex sessions only after Codex restarts or is launched through Headroom; it does not lower tokens already spent in the current session.

headroom wrap codex: Starts a Headroom proxy and launches Codex through it for that one session. Use this when you want the current new Codex session to route through Headroom immediately.

headroom init --global --memory codex: Writes durable user-scope Codex integration so future Codex sessions know about Headroom and its memory/retrieve tooling. `--global` means current Linux user, not just this project folder. `--memory` enables Headroom's local memory layer.

codex mcp list: Shows which MCP tools Codex can use. After Headroom setup, the list should include `headroom`. If a new MCP does not appear, restart Codex.

npx --yes @puppeteer/browsers install chrome@stable --path <folder>: Downloads Chrome-for-Testing into a user-owned folder without needing sudo. `--yes` skips npm confirmation, `chrome@stable` chooses stable Chrome, and `--path` controls where the browser files go.

EBAY_SELLER_HUB_BROWSER_EXECUTABLE=/path/to/chrome: Environment variable used by the Pokemon Seller Hub connector to launch a real Chrome-family browser instead of Playwright's bundled Chromium. This helps with eBay verification/browser fingerprint issues.

timeout 12s command: Runs a command but automatically stops it after 12 seconds. Useful for smoke-testing browser launches so a GUI process does not hang forever.

python3 -m py_compile file.py: Checks whether a Python file can compile without running the whole app. Good for catching syntax/import-shape errors after editing service files.

psql -U user -d database < migration.sql: Applies a SQL migration file to Postgres. In this project it was usually run through `docker exec -i pokemontool_postgres psql ...` so the SQL goes into the Postgres container.

CREATE OR REPLACE FUNCTION in Postgres: Creates or updates a reusable SQL function. We used it for Seller Hub helpers so Go can ask for the latest research metric without duplicating a huge SQL block everywhere.

LEFT JOIN LATERAL: Runs a small subquery once for each row from the main table. In Finder, each slab opportunity row uses it to attach the newest matching Seller Hub ACTIVE and SOLD metric.

jsonb_build_object: Postgres function that builds JSON directly inside SQL. We used it to return Seller Hub metrics as one `sellerHubMetrics` object in the API response.

=========================== END CODEX DEBUG ====================================


=========================== CURRENT PROJECT MAP ====================================
The active app is the card-store system, not NexusOS. For normal work right now think:
PokemonTool = the card brain and vendor decision app
PokeTCG = exact Pokemon card identity and market lookup
Odoo = the public store, products, orders, customers, invoices, and ERP
Hermes = optional operator assistant for reports/research, not in the customer request path
NexusOS = optional broader Shopify/agent platform, useful later but not required for the card store

Default stack to run now:
cd /home/iscjmz/shopify/shopify
scripts/dev-cardstore.sh up
scripts/dev-cardstore.sh health

That starts Odoo + PokemonTool + PokeTCG. It does not start NexusOS, Kafka, Temporal, Qdrant, Ollama, or the heavy browser scraping worker.

Full universe stack:
cd /home/iscjmz/shopify/shopify
scripts/dev-universe.sh up
scripts/dev-universe.sh health

That starts Odoo + NexusOS + PokemonTool + PokeTCG. Use this only when testing the whole root Shopify/NexusOS platform together with the Pokemon/Odoo card store.

Why Nexus is not needed for the card store:
NexusOS is for broader Shopify merchant automation, agent workflows, Kafka/Temporal experiments, AI routes, and cross-shop workflows. The actual card selling path is already PokemonTool -> Odoo. If we are adding card pricing, card sourcing, inventory approval, Odoo product sync, storefront filters, Seller Hub evidence, or vendor alerts, build it in PokemonTool/Odoo first.

Why Odoo matters:
Odoo is not the card research brain. Odoo is the store/ERP layer. It should hold products that are approved for sale, show the public storefront, handle orders, customers, invoices, refunds, and back-office product metadata. PokemonTool decides what is worth listing; Odoo sells and manages it.

Why PokeTCG matters:
PokeTCG stops the app from treating "Charizard" as one generic product. It returns exact variants like card id, set, number, and market fields. That exact identity is what lets watchlists, inventory, alerts, and slab logic avoid false matches.

=========================== CURRENT COMMANDS ====================================
scripts/dev-cardstore.sh up: starts the focused card-store stack. This is the default command for Pokemon/Odoo work.
scripts/dev-cardstore.sh health: checks Odoo storefront, Pokemon API, Pokemon web, and PokeTCG search.
scripts/dev-cardstore.sh ps: shows containers for the focused stack.
scripts/dev-cardstore.sh down: stops the focused stack.
scripts/dev-cardstore.sh scraping-up: starts optional Facebook/Mercari browser scraping.
scripts/dev-cardstore.sh scraping-down: stops optional browser scraping.
scripts/dev-cardstore.sh up-with-scraping: starts the focused stack plus optional browser scraping.

scripts/dev-universe.sh up: starts Odoo + NexusOS + PokemonTool together.
scripts/dev-universe.sh health: checks all main endpoints across the full universe.
scripts/dev-universe.sh ps: shows all universe containers.
scripts/dev-universe.sh down: stops the full universe.

When to use which:
Use dev-cardstore for normal card-store development.
Use dev-universe only when you need NexusOS.
Use scraping-up only when testing Facebook/Mercari scraping. Do not leave it running for normal work because browser automation is heavier and those sites are brittle.

=========================== WHY DOCKER COULD NOT RUN TOGETHER BEFORE ====================================
Before the local universe files, multiple compose stacks wanted the same host ports. Example: Postgres commonly wants 5432, Redis wants 6379, web apps want 3000/5173, and monitoring tools also expose ports. Docker cannot bind two containers to the same host port at the same time.

The fix was not to smash everything into one giant compose file. The fix was:
1. Keep each product stack in its own compose file.
2. Add override files for local non-conflicting host ports.
3. Create a shared external Docker network called pokemon-odoo-bridge where cross-stack services need to talk.
4. Add wrapper scripts so you do not have to remember every compose file and port override.

What changed:
docker-compose.odoo.yml now uses the external pokemon-odoo-bridge network.
docker-compose.universe.yml assigns NexusOS local ports that do not collide with Pokemon/Odoo.
Pokemon/docker-compose.universe.yml assigns Pokemon local ports that do not collide with Odoo/Nexus.
scripts/dev-universe.sh creates/reuses the shared network and starts each stack in the right order.
scripts/dev-cardstore.sh starts only the useful card-store pieces by default.

Important Docker rule:
Inside a container, 127.0.0.1 means that same container, not your laptop and not another container. Containers should call each other by service name on a shared Docker network, like http://poketcg:8765 or http://shopify-odoo:8069.

Host ports are for your browser or terminal:
http://127.0.0.1:5173 means your laptop reaches the Pokemon web container.
http://127.0.0.1:8069 means your laptop reaches Odoo.
http://poketcg:8765 means a Docker container reaches the PokeTCG container.

=========================== CURRENT LOCAL URLS ====================================
Pokemon dashboard: http://127.0.0.1:5173
Pokemon API: http://127.0.0.1:3001
PokeTCG: http://127.0.0.1:8765
Odoo storefront: http://127.0.0.1:8069/pokecard-store
Odoo login: http://127.0.0.1:8069/web/login?db=pokecard_store
RabbitMQ UI: http://127.0.0.1:15673
Grafana: http://127.0.0.1:3002
Prometheus: http://127.0.0.1:9091

NexusOS only when using dev-universe:
Nexus web: http://127.0.0.1:3000
Nexus gateway: http://127.0.0.1:8080
Nexus AI: http://127.0.0.1:8000
Temporal UI: http://127.0.0.1:8088
Qdrant: http://127.0.0.1:6333

=========================== SEARCHING A CARD - WHAT ACTUALLY HAPPENS ====================================
When you type a card name in the UI:
React UI calls the Go API.
Go API calls PokeTCG.
PokeTCG returns exact card variants with set/card/market fields.
You select the exact result.
Then the app can save a watchlist row or inventory row with exact card metadata.

After a watchlist target exists:
api-consumer reads internal watchlist targets from the Go API.
api-consumer searches eBay Browse API for active listings.
api-consumer filters listings by card name, set, card number, grade, language, and raw/slab lane.
Matched listings go to RabbitMQ.
The Go worker consumes RabbitMQ messages.
The Go worker writes listing snapshots, creates deduped alerts, and pushes live SSE events to the frontend.

Seller Hub Product Research is separate:
It uses your local logged-in browser profile.
It can read ACTIVE and SOLD Product Research metrics.
It stores snapshots in Postgres.
It is stronger evidence than active listing asks because SOLD means buyers actually paid.
It should not run on every keystroke. Use it for selected targets, batch Finder targets, and serious sourcing evidence.

Scrapling is separate too:
Scrapling is selector-based HTML extraction for approved pages with known CSS selectors.
It is wired and tested, but it is not the default eBay path.
If eBay blocks a page with 403, Scrapling cannot magically bypass that. It is a tool for known allowed pages, dry-runs, and extra sold-comp sources.

=========================== WHY BROWSER SCRAPING IS OPTIONAL ====================================
Facebook Marketplace and Mercari scraping use browser automation. That means a headless browser starts, loads real pages, waits for selectors, parses results, and publishes listing messages. This is heavier than API calls and more likely to break when a website changes HTML, blocks automation, or requires login.

That is why scraping-service is behind the browser-scraping Compose profile. Normal development should not pay that CPU/RAM cost. Turn it on only when testing those marketplace paths.

=========================== SECURITY CHANGES MADE ====================================
Pokemon/client/nginx.conf now sends browser security headers:
Content-Security-Policy: limits what scripts/images/connections the frontend can use.
X-Frame-Options: stops the app from being embedded in another site.
X-Content-Type-Options: stops MIME sniffing.
Referrer-Policy: limits referrer leakage.
Permissions-Policy: blocks unused browser permissions like camera/microphone/geolocation/payment.

Current remaining security work before real public production:
Move frontend JWT storage away from localStorage.
Replace SSE token-in-query behavior with short-lived stream tokens.
Keep eBay/Odoo/Shopify/database credentials only in env files or a secret manager.
Do not store Seller Hub browser cookies in Postgres or git.
Run security review before exposing any service beyond localhost.

=========================== GIT / DIFF WORKFLOW ====================================
git status --short: shows changed files in the smallest useful format.
git diff -- file: shows exactly what changed in one file.
git diff --stat: shows a summary of changed files and line counts.
git diff --check: catches whitespace errors before commit.
git log --oneline -n 10: shows recent commits.
git branch --show-current: shows current branch.

How to think about git diff:
A diff shows removed lines with "-" and added lines with "+". It is the proof of what changed. Before committing or asking someone to trust a change, inspect the diff for accidental secrets, unrelated edits, huge generated files, and broken config.

Do not run destructive git commands unless you mean it:
git reset --hard deletes local changes.
git checkout -- file replaces a file with the version from git.
Those can wipe useful work, so use them only intentionally.

=========================== CURRENT OPEN PRODUCT WORK ====================================
The local stack can run. The big product work is not "more containers"; it is better product trust and workflow:
Fix data freshness for price_history and deals.
Add visible freshness state in the dashboard.
Make Odoo sync report exactly what is READY, SYNCED, FAILED, STALE, or NEEDS_REPRICE.
Add storefront filters for raw/slab/sealed, set, grade, condition, and price range.
Make pricing decisions depend on exact identity, SOLD evidence, Seller Hub snapshots, fees, shipping, and margin.
Keep browser scraping optional until selectors/sessions are hardened.
Add E2E tests once Chrome/Playwright is available on the machine.

=========================== PLANE PROJECT MANAGEMENT ====================================
Plane is like a self-hosted Jira/Linear style project-management app. It is not GitHub and it is not part of the Pokemon/Odoo runtime.

What Plane is good for:
- work items/tasks
- cycles/sprints
- modules/roadmaps
- product specs and notes through Pages
- triage and execution tracking
- keeping product decisions out of chat history

What GitHub is good for:
- code
- branches
- commits
- pull requests
- code review
- CI checks
- release history

Big tech usually uses both:
Jira or similar tool for product/project tracking, GitHub/GitLab/Bitbucket/internal Git for code, and Confluence/Notion/Google Docs/GitHub markdown for docs. Plane can replace the Jira/Linear part for this local project.

Where Plane is installed:
/home/iscjmz/ops/plane-selfhost

Why not inside /home/iscjmz/shopify/shopify:
Plane is a full third-party AGPL app with its own Docker stack, database, queue, object storage, frontend, backend, and proxy. It should stay outside the Shopify repo. The repo can document how we use Plane, but it should not vendor Plane source/runtime files.

Plane local URL:
http://localhost:8095

Plane commands:
/home/iscjmz/ops/plane-selfhost/plane.sh start
/home/iscjmz/ops/plane-selfhost/plane.sh status
/home/iscjmz/ops/plane-selfhost/plane.sh logs api
/home/iscjmz/ops/plane-selfhost/plane.sh stop
/home/iscjmz/ops/plane-selfhost/plane.sh backup

Plane services:
web, admin, space, api, worker, beat-worker, migrator, live, Postgres, Valkey/Redis, RabbitMQ, MinIO, proxy.

Local safety choices:
Plane uses ports 8095 and 8445 so it does not collide with Pokemon/Odoo/Nexus.
Plane proxy is bound to 127.0.0.1 only.
Plane env secrets are local in /home/iscjmz/ops/plane-selfhost/plane-app/plane.env and must not be committed or pasted.

Recommended workspace:
Workspace: Card Vendor OS
Projects: PokemonTool, Odoo Storefront, PokeTCG Identity, Marketplace Research, Infrastructure/Ops, Security/Compliance, Documentation
Modules: Watchlist and Alerts, Seller Hub Research, eBay Browse API, Scrapling/Sold Comps, Inventory to Odoo Sync, Storefront Search and Filters, Data Freshness, Auth and Session Hardening

Use Plane when planning work. Stop Plane when the machine is warm and you are just coding Pokemon/Odoo.

