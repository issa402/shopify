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

===================== GITHUB / GIT HOOKS ========================
.githooks/: This is a folder for custom Git hooks. Git hooks are small scripts that Git runs automatically at certain moments. This is DevOps work, but it is local DevOps, meaning it runs on your laptop before GitHub sees anything. CI/CD usually runs in GitHub Actions after code is pushed or opened in a pull request. Git hooks are earlier protection.

Why we made this: GitHub blocks files over 100 MB. If you accidentally commit a huge zip, video, database, docker output, or random generated file, GitHub can reject the push. The hook setup blocks big files before they get into the repo history or before they upload.

core.hooksPath .githooks: Git normally looks for hooks inside .git/hooks, but that folder is not committed to the repo. By running `git config core.hooksPath .githooks`, we told this repo to use the tracked `.githooks/` folder instead. That means the hook files can live in the project and be reviewed like normal code.

.githooks/pre-commit: This runs before `git commit` finishes. It checks the files that are staged with `git add`. If a staged file is too big, Git stops the commit. This protects the repo before the huge file enters Git history.

.githooks/pre-push: This runs before `git push` uploads commits to GitHub. It checks the commit range Git is about to push. This matters because a big file can exist in history even if you deleted it later. GitHub still sees it during push, so the pre-push hook catches that.

scripts/check-large-files.sh: This is the main Bash script with the real logic. The hook files are small on purpose. They just move to the repo root and call this script. This is cleaner because both hooks share one script instead of copying the same code twice.

LARGE_FILE_LIMIT_BYTES: This variable controls the max file size. We set it to `52428800`, which is 50 MB. GitHub rejects at 100 MB, so 50 MB is a safer warning line.

`#!/usr/bin/env bash`: This is called a shebang. It tells Linux to run the file with Bash.

`set -euo pipefail`: This makes Bash stricter. `-e` means stop if a command fails. `-u` means error if you use a variable that was never set. `pipefail` means if one command inside a pipeline fails, the full pipeline counts as failed.

`readonly LIMIT_BYTES="${LARGE_FILE_LIMIT_BYTES:-52428800}"`: This creates a variable that cannot be changed later. The `${VAR:-default}` syntax means use `LARGE_FILE_LIMIT_BYTES` if it exists, otherwise use `52428800`.

`bytes_to_mib() { ... }`: This defines a Bash function. We use it to turn raw bytes into a human-readable number like 50.0 MiB.

`awk -v bytes="$1" 'BEGIN { printf "%.1f MiB", bytes / 1024 / 1024 }'`: `awk` is a text/math tool. `-v bytes="$1"` passes the function argument into awk. `$1` means the first argument given to the Bash function. `printf "%.1f MiB"` prints one decimal place.

`>&2`: This means print to stderr instead of normal output. Error messages should go to stderr because Git treats them like failure messages.

`check_staged_files()`: This function checks files currently staged for commit.

`git diff --cached --name-only --diff-filter=ACMR`: This lists staged files only. `--cached` means staged/index, not just working tree. `--name-only` prints paths only. `--diff-filter=ACMR` means Added, Copied, Modified, Renamed files. Deleted files do not need a size check.

`while IFS= read -r path; do ... done`: This reads file paths line by line. `IFS=` helps preserve spaces. `-r` means do not treat backslashes as escape characters.

`[[ -f "$path" ]] || continue`: This means if the path is not a regular file, skip it. This avoids errors for deleted files, folders, or submodule entries.

`stat -c '%s' "$path"`: This gets the file size in bytes.

`if (( size > LIMIT_BYTES )); then`: Double parentheses are Bash math mode. This checks if the file is bigger than the limit.

`failed=1`: We do not instantly exit on the first big file. We mark failed so the script can report everything it finds, then return failure at the end.

`check_object_range()`: This checks actual Git objects in commits. That is deeper than checking normal files, because Git push sends objects from commit history.

`git rev-list --objects "$range"`: This lists every Git object in the commit range being pushed. A range like `oldsha..newsha` means everything in the new commit side that the remote does not have yet.

`git cat-file -t "$object"`: This asks Git what type of object it is. We only care about `blob` objects because blobs are file contents.

`git cat-file -s "$object"`: This asks Git for the blob size in bytes.

`${path:-$object}`: This means use the file path if Git gave us one; if not, show the raw object hash.

`check_pre_push_ranges()`: This reads data that Git automatically sends to a pre-push hook. Git gives local branch name, local commit SHA, remote branch name, and remote commit SHA.

`0000000000000000000000000000000000000000`: In Git hook input, all zeroes can mean a branch is being created or deleted. If local SHA is all zeroes, that is a delete push, so we skip it.

`range="${remote_sha}..${local_sha}"`: This builds the exact commit range that is about to upload.

`case "${1:-}" in`: This checks the first argument passed to the script. `--staged` means run the commit check. `--pre-push` means run the push check.

Overall flow:
1. You run `git add`.
2. You run `git commit`.
3. `.githooks/pre-commit` runs automatically.
4. It calls `scripts/check-large-files.sh --staged`.
5. If no staged file is over 50 MB, the commit continues.
6. You run `git push`.
7. `.githooks/pre-push` runs automatically.
8. It calls `scripts/check-large-files.sh --pre-push`.
9. If no pushed blob is over 50 MB, Git uploads to GitHub.
10. If something is too big, Git stops and prints the bad file.

Important mental model: `.gitignore` prevents new unwanted files from being added by accident. Git hooks enforce rules when you commit or push. GitHub Actions / CI/CD runs after code reaches GitHub. So the order is `.gitignore` first, hooks second, CI/CD third.





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






========================== POKEMON PYTHON STACK ==========================
Everything for python is under services/
ONLY IN analytics-engine and api-consumer




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







Code for data freshness in pokemon postgres

