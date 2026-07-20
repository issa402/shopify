====================RABBITMQ_PUBLISHER================================
Rabbitmq_publisher : So we use a TCP connection to RabbitMQ broker. Create channels which don not create a new TCP connection. THE RABIITMQ FILE CONTAIN THE ETHODS FOR THE SERVICE FILES (EBAY AND TCG). EVERYHTING INITILAIZED IN RABBITMQ IS CALLED IN MAIN(THE ORCHESTRATOR AND ONCE MAIN CREATES A RABBITMQ PUBLISHER IT THEN PASSES INTO EBAY SERVICES AND TCG SERVICES IN THEIR RESPECTED INIT FUNCTIONS. FROM THERE INSIDE THOSE SERVICE FILES THEY CALL METHODS FROM rabbitmqpublisher SUCH AS **await self.publisher.publish("listings", payload)** USED FOR SINGLTETON USE THATS WHY GLOBAL IS CALLED **global publisher, ebay_svc, tcg_svc** AND HERE PUBLISHER IS INITIALIZED **publisher = RabbitMQPublisher(rabbitmq_url)** THEN PASSED TO THE SERVICE LAYER **ebay_svc = EbayService(repo=EbayRepo(), publisher=publisher) tcg_svc = TCGService(repo=TCGRepo(), publisher=publisher)**.


queue_report.py: SCRIPT TO CHECK IF RABBITMQ IS UP AND RUNNING HEALTHY. FIRST CONNECTS TO RABBITAMQP AND RABBITMGMT WHICH IS A MANAGMENT TOOL TO SEE RABBITMQ DIAGNOSTICS BY LOGGING IN WITH USERNAME AND PASSWORD. CLASS QUEUEREPORTER TAKES IN TWO ARGUMENTS WHIHC ARE CONNECTION URLS. ASYNC DEF CHECK CONNECTION CONNETCS TO AMQP. CHECK QUEUES AMQP TAKES IN THE QUEUE NAME WHCIH IS ONLY listing we only have one queue name and that can be confirmed in TCG AND EBAY SERVCIES WHERE THEY APPENDED A LISTING PAYLOAD CALLED LISTINGS. IT CHECKS FOR EACH QNAME. ALSO aio_pika talks to RabbitMq and httpx handles the HTTP requests for the Mnagment Rabbitmq. SO FIRST IT OPENS A CONNECTION THEN A CHANNEL IT ITERATES THROUGH EACH QUEUE NAME IF EXISTS BY using **channel.declare_queue(passive =True)** which means dont touch it just inspect.  the **queue.declarations_result.message_count** checks how many messages are inside the 'listing' queue. The **declaration_result.consumer_count** checks how many messages are sitting in the listings queue. Inside it also chceks if that specific queue names exists if Not rabbitmq kills the channel and onto the next queue and once outer loop existed returns error if couldnt expect queues. The CHECK_MGMT_STATS it first opens a HTTP client . Then hits the the rabbitmq web api  using client.get . Initialzie data to grab all json and then using data.get for the paremeter queue totals and parse the JSN to find the total message count across eveyr queue on the server not just one named listing. Then finally main creates an insnace of the QUEUEReporter and runs the functions inside using await. EVERY PYTHON FILE WILL ALWAYS BE MAIN ITS JUST HOW ETHYRE PORGRAMMED SO IF NAME WILL ALWAYS EQUAL MAIN. **Asyncio.run(main())** means stars the asynchronous event loop to power all await commands

RabbitMQ in PokemonTool now: RabbitMQ is not an eBay webhook. RabbitMQ is the internal message bus. The Python api-consumer scans eBay/PokeTCG on a schedule or immediate trigger, publishes listing messages into RabbitMQ, and the Go server worker consumes those messages. The Go worker then writes alerts/card listing snapshots into Postgres and pushes live frontend notifications through SSE. If RabbitMQ is running all night but the scanner does not publish a new listing, RabbitMQ alone does not create new alerts.

30 minute scanner loop: SCRAPING_INTERVAL_MINUTES controls the regular scanner interval. We also added immediate scan behavior when a user adds a new watchlist item, so the user should not always have to wait for the 30 minute loop after adding a new card.

Alert dedupe: eBay itemId is stored as listing_id. Alerts use a unique partial index on user_id + marketplace + listing_id so the same eBay listing should not keep creating duplicate alerts every 30 minutes.

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
git branch: shows local branches and the star means the current branch
git pull: only works cleanly when the current branch has upstream tracking set
git pull origin infra_future_standard: pulls branch infra_future_standard from remote named origin
git branch --set-upstream-to=origin/infra_future_standard infra_future_standard: tells Git that local branch infra_future_standard tracks origin/infra_future_standard
Why git pull failed before: typing git pull infra_future_standard treated infra_future_standard like a remote repository name, not a branch name. Git expects git pull REMOTE BRANCH, like git pull origin infra_future_standard.

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
cat /etc/group : shows all groups
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
docker compose -f docker-compose.yml -f docker-compose.selfhost.yml up -d postgres redis rabbitmq poketcg server api-consumer client: starts only the required Pokemon self-host services and skips optional broken services
docker compose -f docker-compose.yml -f docker-compose.selfhost.yml stop: stops the Pokemon self-host stack
docker compose -f docker-compose.yml -f docker-compose.selfhost.yml ps: shows status of the Pokemon self-host stack
docker stop pokemontool_client: stops only the LAN-facing Pokemon frontend container
docker stop shopify-web-1 shopify-gateway-1 shopify-ai-1: stops only the three root Shopify app containers by exact container name
docker compose -f docker-compose.dev.yml stop web gateway ai: stops the three Shopify app services through the correct root compose file
docker inspect {container_name}: inspect everythign in the contianer for image to network everything
We made services talk to local host only by doing this :  ports: - "127.0.0.1:5432:5432" 
We made the Pokemon self host safer by doing this: client uses "0.0.0.0:5173:80" so a LAN/VPN browser can reach the app, but server uses "127.0.0.1:3001:3001" so the Go API is not directly open to the LAN. The client nginx proxies /api to server:3001 inside Docker.
Use sudo ss -tulpn to see the services running You will now see: cp    LISTEN  0        4096           127.0.0.1:5672           0.0.0.0:* (Means who am i talking to )     users:(("docker-proxy",pid=1665170,fd=7))  
ss -ltnp: shows listening TCP ports. 0.0.0.0:5173 means every network interface on this machine can receive traffic for that port. 127.0.0.1:3001 means only this same machine can reach that port.
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
docker compose config: renders the final merged compose config after all -f files and overrides. This is how we confirmed the self-host override changed server ports instead of accidentally duplicating them.
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
Important internet mental model: 0.0.0.0 on your laptop does not automatically mean the whole internet can reach it. It means the laptop accepts traffic on all its own interfaces. For a random person outside your house to reach it, your router also needs to forward a public port to the laptop, or you need a tunnel/VPN/funnel service, or the laptop must have a real public IP.
In docker compose-yml always include : restart: unless-stopped; So that the containers auto start after the VM rebooot and any crash
docker compose down: stops contianers
docker compose up -d --build: Rebuilds backend image and restarts containers with new image
In the dockerfile create adduser and a non root user also change ownership so the user can read the files and switch to the non root user and insdie the docker-compose.yml update it so backend is read only and cap_drop drops all linux capabilities and cap add only allows binding to low ports if needed,must rebuild aftewards 
docker exec -it backend sh: creates a shell inside backend so you can run whoami






========================== POKEMON PYTHON STACK ==========================
Everything for python is under services/
ONLY IN analytics-engine and api-consumer

========================== POKEMON APP / POKETCG / EBAY ==========================
PokemonTool is the card market intelligence app. The main product loop is: user searches a card with PokeTCG, selects the exact card/set, sees market price, chooses a target below market, and the scanner looks for eBay listings at or under that target.

PokeTCG is the exact card + raw market price source. It gives things like card ID, set, number, image, tcgplayer market, cardmarket trend, and updated dates. It is the heart of exact card selection because "Charizard" by itself is too vague.

eBay is the active listing source. eBay is where we look for real current listings, especially slabs, because PokeTCG raw price data does not give complete graded/slab market data.

Raw vs slab logic: RAW watchlist rows should not alert on slab listings. SLAB rows should match a specific slab tier like PSA_10 or PSA_9. ALL_SLABS creates scan targets for major grades like PSA 10/9/8/7, CGC 10/9.5/9, and BGS 10/9.5/9.

Language preference: watchlist/live eBay lookup supports BOTH, ENGLISH, or JAPANESE. This is title based because eBay listings do not always give perfect structured language data. Japanese detection uses title terms like Japanese, Japan, JP, JPN, Split Earth, E4, and Pokemon Card Game. English detection uses terms like English, ENG, WOTC, and Black Star Promo.

Slab snapshots: card_listings stores active eBay observations by card ID, slab tier, price, title, URL, and language. The frontend slab summary shows the cheapest observed listings per tier. If a tier looks weird, like PSA 9 higher/lower than 9.5, remember these are active listing asks, not guaranteed sold comps or fair market value.

Live eBay lookup: user-clicked lookup can search deeper than the background scanner. Background scans stay cheaper to protect eBay API quota. More pages means more eBay API calls. Showing more listings from the same returned page does not cost extra; fetching page 2/3/etc costs more API calls.

Self host client URL right now: http://192.168.1.12:5173 when the client is running in self-host mode on this LAN. Another device on the same LAN can try that. A phone on cellular cannot use 192.168.1.12 because that is a private LAN IP.




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
apt-mark showmanual: shows things explicitly added and installed

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

LAN exposure vs internet exposure: LAN exposure means another device on your Wi-Fi/private network can connect to your laptop. Internet exposure means someone outside your router can connect from the public internet. Binding Docker to 0.0.0.0 can expose a port to LAN, but it usually does not expose it to the whole internet unless the router forwards that port or a tunnel/VPN/funnel is running.

Private IPs like 192.168.x.x, 10.x.x.x, and 172.16-31.x.x are not routable from the public internet. If your app URL is http://192.168.1.12:5173, only devices that can route into that private network can reach it.

Safe friend test order:
1. Start Pokemon self-host core services.
2. Keep only client on 0.0.0.0:5173.
3. Keep Go API, Postgres, Redis, RabbitMQ on 127.0.0.1 or Docker internal network.
4. Test from another device on same Wi-Fi.
5. If different Wi-Fi blocks it, use Tailscale/ZeroTier VPN.
6. Only later consider public reverse proxy with HTTPS.

Reverse proxy: Nginx/Caddy/Traefik sits in front of the app and becomes the only public entrypoint. It can terminate HTTPS on port 443 and forward requests internally to the client/API. This is better than exposing every container port.

VPN: Tailscale/ZeroTier style access creates a private network between trusted devices. This is best for friends/testers because no router port forward is needed and Postgres/Redis/RabbitMQ stay private.

Hysteria: Hysteria is a fast QUIC-based proxy/VPN-like tool. It is high value for censorship resistance, unreliable networks, UDP/QUIC performance, SOCKS/HTTP proxying, TUN mode, and advanced proxy forwarding. It is not the simplest first choice for this app because a normal browser user usually still needs a Hysteria client/profile, and if you are behind home NAT it does not magically make your laptop public unless there is a reachable endpoint or port forwarding/tunnel path. For our current goal, Tailscale is simpler for private friend testing, and Caddy/Nginx reverse proxy is cleaner for real public web hosting.

##### TAILSCALE VPN SELF HOST TEST #####
Tailscale is the VPN choice we used so a friend can access the Pokemon app from another network without exposing the whole app to the public internet. Tailscale gives this Linux machine a private VPN IP that starts with 100.x.x.x. Only devices in the same tailnet can reach that IP.

curl -fsSL https://tailscale.com/install.sh -o /tmp/tailscale-install.sh: downloads the official Tailscale install script into /tmp. curl gets the file from the internet, -f fails on HTTP errors, -s is silent, -S still shows errors, -L follows redirects, and -o writes the output to that file.

sudo sh /tmp/tailscale-install.sh: runs the installer as root because Tailscale needs to install packages and create a system service/network interface.

sudo tailscale up: starts Tailscale login/authentication. It prints a login URL. Open that URL in the browser, sign in, and approve the machine into your tailnet.

Login successful: means this computer joined the tailnet correctly.

tailscale ip -4: prints this machine's IPv4 Tailscale IP. In our test it returned 100.91.97.106.

100.91.97.106: this is the private Tailscale VPN IP for iscjmz-ThinkPad-T14s-Gen-1. Friends on the same tailnet should use this IP, not the LAN IP.

docker compose -f docker-compose.yml -f docker-compose.selfhost.yml up -d postgres redis rabbitmq poketcg server api-consumer client: starts the Pokemon services needed for friend testing. The -f flags merge the normal compose file with the self-host override. We intentionally start only core services and skip optional broken services.

curl -I http://127.0.0.1:5173: checks if the Pokemon client responds locally on this same machine. HTTP/1.1 200 OK means nginx served the frontend.

curl -I http://100.91.97.106:5173: checks if the Pokemon client responds through the Tailscale IP. HTTP/1.1 200 OK means the app is reachable over the VPN address.

ss -ltnp: shows listening TCP ports. In our safe self-host state, 0.0.0.0:5173 is the frontend exposed to LAN/VPN, and 127.0.0.1:3001, 127.0.0.1:5432, 127.0.0.1:6379, 127.0.0.1:5672 are backend/database/queue ports kept local-only.

http://100.91.97.106:5173: this is the URL to give a friend after they install Tailscale and join the same tailnet.

Friend flow: friend installs Tailscale, logs in or accepts the invite/share, confirms they are in the same tailnet, then opens http://100.91.97.106:5173 in their browser.

Important: Tailscale IP 100.91.97.106 is for remote VPN access. LAN IP 192.168.1.12 is only for devices on the same Wi-Fi/LAN. Public internet users cannot use 192.168.1.12.

Security shape from our test: friend browser -> Tailscale VPN -> 100.91.97.106:5173 -> Docker client nginx -> private Docker server:3001 -> Postgres/Redis/RabbitMQ/PokeTCG internal services.

docker stop pokemontool_client: emergency stop for the only network-facing Pokemon frontend. If worried about access, stop this first.

docker compose -f docker-compose.yml -f docker-compose.selfhost.yml stop: stops the Pokemon self-host stack.

Public internet checklist before exposing:
- no dev auth bypass
- HTTPS only
- strong JWT/app secrets
- no Postgres/Redis/RabbitMQ exposed
- no RabbitMQ management UI exposed
- API rate limits
- logs checked for secrets
- backups for Postgres
- eBay API quota understood

============================ SHOPIFY / BUSINESS DIRECTION ==========================
PokemonTool is the market intelligence engine. Shopify should be the commerce engine. Do not force them together until the workflow is clear.

PokemonTool should handle exact card lookup, market price, eBay/slab observations, under-market alerts, inventory valuation, cost basis, and repricing ideas.

Shopify should handle storefront, draft products, checkout, orders, customer history, seller subscriptions, and seller operations.

First useful Shopify feature: Pokemon inventory item -> Prepare Listing -> suggested price/margin -> create Shopify draft product -> seller reviews and publishes in Shopify.

The stronger business is not a generic price checker. The stronger business is seller workflow: find underpriced cards, alert fast, track inventory, estimate margin, create listings, and help sellers reprice/sell faster.





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





=========================== INFRASTRUCTURE ENGINEERING EXPLAINED ===========================

This section is the big mental model for infrastructure engineering.

Infrastructure is the layer that makes software run reliably somewhere other than your brain or your laptop. It covers servers, containers, networks, databases, queues, secrets, config, deploys, logs, backups, monitoring, security, and recovery.

The job is not just "make the app start." The job is:

- make the app start the same way every time
- make it easy to deploy
- make it obvious when it is broken
- make it safe to change
- make it recoverable when something fails
- make it hard to accidentally destroy data
- make different environments predictable

The most important infra pattern is:

preflight -> execute -> verify -> observe -> rollback if needed

Preflight means check before changing anything.
Execute means do the change.
Verify means prove the change worked.
Observe means watch logs, metrics, health, and user-facing behavior.
Rollback means have a known way back if the change is bad.

Every serious infra script should answer:

- What am I changing?
- What do I depend on?
- Can I run this twice safely?
- How do I know it worked?
- What logs or report do I produce?
- What happens if it fails halfway?
- How do I undo it?

That is the real infra mindset.

Scripts Infra Engineers Actually Write

  The core categories:

  1. Bootstrap / setup scripts
      - install packages
      - create users/groups
      - create directories
      - set permissions
      - install Docker/agents/tools
      - write baseline config

  Examples:

  setup-server.sh
  install-docker.sh
  create-app-user.sh
  bootstrap-dev-machine.sh

  2. Deploy scripts
      - pull image or artifact
      - load env vars
      - run migrations
      - restart service
      - wait for health check
      - print logs if failed

  deploy.sh
  deploy-staging.sh
  deploy-prod.sh
  rollback.sh

  3. Health check scripts
      - check HTTP endpoints
      - check DB connection
      - check Redis/queue
      - check disk/memory/CPU
      - check service process is alive

  health-check.sh
  smoke-test.sh
  dependency-check.sh
  readiness-check.sh

  4. Backup / restore scripts
      - dump Postgres
      - copy files to storage
      - rotate old backups
      - restore into staging
      - verify backup integrity

  backup-postgres.sh
  restore-postgres.sh
  backup-volume.sh
  backup-retention.sh

  5. Migration scripts
      - apply DB migrations
      - check migration status
      - backfill data
      - verify row counts
      - rollback migration if supported

  migrate.sh
  migration-status.sh
  backfill-users.py
  verify-migration.sql

  6. Log scripts
      - tail service logs
      - search errors
      - summarize failures
      - collect logs into incident bundle

  logs.sh
  grep-errors.sh
  incident-snapshot.sh
  collect-debug-bundle.sh

  7. Monitoring / alert scripts
      - check disk threshold
      - check cert expiration
      - check queue depth
      - check API latency
      - send Slack/email alert

  check-disk.sh
  check-cert-expiry.sh
  check-queue-depth.py
  alert-webhook.sh

  8. Security scripts
      - scan for secrets
      - check open ports
      - audit SSH config
      - verify file permissions
      - rotate keys/tokens

  secrets-scan.sh
  open-port-audit.sh
  ssh-hardening.sh
  permission-audit.sh
  rotate-secret.sh

  9. Docker / container scripts
      - compose up/down
      - rebuild service
      - prune safely
      - inspect container health
      - run one-off commands inside containers

  compose-up.sh
  compose-down.sh
  rebuild-service.sh
  container-health.sh
  docker-clean-safe.sh

  10. CI/CD scripts

  - run lint/tests
  - build image
  - tag image
  - push image
  - deploy from CI
  - validate release

  ci-test.sh
  build-image.sh
  tag-release.sh
  push-image.sh
  release-check.sh

  11. Network scripts

  - check ports
  - DNS lookup
  - TLS test
  - ping/traceroute
  - firewall rule check

  port-check.sh
  dns-check.sh
  tls-check.sh
  firewall-audit.sh
  connectivity-check.sh

  12. Provisioning scripts

  - create VM/server resources
  - install base runtime
  - create systemd service
  - configure reverse proxy
  - configure firewall

  provision-vm.sh
  install-systemd-service.sh
  setup-nginx.sh
  setup-caddy.sh
  configure-firewall.sh

  The Must-Know Stack

  You should know how to write these in Bash first:

  setup
  deploy
  rollback
  health check
  backup
  restore
  migrate
  logs
  incident snapshot
  port preflight
  secrets audit
  docker compose wrapper

  Then Python for scripts that need parsing, APIs, JSON, reports, or more logic:

  inventory reports
  cloud API automation
  log parsers
  backup verification
  health dashboards
  queue monitors
  config validators

  The real infra engineer pattern is:

  preflight -> execute -> verify -> log -> rollback path

  Every serious script should answer:

  What am I changing?
  Can I run twice safely?
  How do I know it worked?
  What do I print if it fails?
  How do I undo it?


=========================== ENVIRONMENTS: DEV, STAGING, PROD ===========================

An environment is a place where the system runs with its own config, data, network, services, and rules.

Development, usually called dev, is where engineers build and test. It can be local on your laptop or shared in the cloud. Dev is allowed to be messy. It is okay if dev breaks because real users are not depending on it.

Development examples:

- local Docker Compose stack
- local Postgres database
- test API keys
- fake users
- fast reload frontend
- debug logs enabled
- weak local passwords only for local use

Staging is a production-like test environment. It should be close to prod, but it should not contain real customer damage risk. Staging exists to catch integration problems before prod.

Staging examples:

- same Docker image as prod
- same migration process as prod
- same reverse proxy style as prod
- same queue/background worker setup as prod
- test payment mode
- fake or sanitized data
- real monitoring if possible

Production, usually called prod, is the real system. Real users, real data, real money, real reputation. Prod changes need discipline.

Production examples:

- real domain name
- real database
- real secrets
- real payment/webhook credentials
- restricted SSH access
- backups enabled
- monitoring and alerts enabled
- rollback path documented
- migrations reviewed before running

The reason people separate environments is because the same app needs different behavior in different places.

Example:

```text
local dev:
  database = localhost:5432
  logging = debug
  payment = test mode

production:
  database = private-prod-db.internal
  logging = info/warn/error
  payment = live mode
```

Same code, different config.


=========================== CONFIGS: WHAT THEY ARE ===========================

Config means the values that tell software how to behave in a specific environment.

Code is the logic.
Config is the environment-specific settings.

Code says:

```text
connect to the database
```

Config says:

```text
database host = postgres
database port = 5432
database name = pokemontool
database user = pokemontool_user
```

Common config values:

- database URL
- Redis URL
- RabbitMQ URL
- port number
- API base URL
- allowed frontend URL for CORS
- log level
- feature flags
- timeout values
- retry counts
- queue names
- region names
- cloud bucket names
- webhook URLs
- secret names

Secrets are a special kind of config. Secrets are config values that can hurt you if leaked.

Secrets include:

- passwords
- API keys
- OAuth client secrets
- JWT signing secrets
- encryption keys
- webhook signing secrets
- database URLs with passwords inside
- private keys
- cloud credentials

Normal config can sometimes be committed. Secrets should not be committed.

Good normal config example:

```text
PORT=3001
LOG_LEVEL=info
CLIENT_URL=http://localhost:5173
```

Dangerous secret example:

```text
OPENAI_API_KEY=real_key_here
DATABASE_URL=postgres://real_user:real_password@prod-db:5432/app
```

How configs are usually set:

- `.env` files for local development
- environment variables in Docker Compose
- GitHub Actions secrets in CI
- Kubernetes ConfigMaps and Secrets
- Terraform variables
- cloud secret managers
- systemd EnvironmentFile files

In Docker Compose, config often looks like:

```yaml
services:
  server:
    environment:
      PORT: "3001"
      POSTGRES_HOST: postgres
      REDIS_URL: redis://redis:6379
```

Inside a container, `localhost` means that same container. That is why a container usually connects to `postgres`, not `localhost`, when Postgres is another service in the same compose file.

Good container config:

```text
POSTGRES_HOST=postgres
REDIS_URL=redis://redis:6379
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672
```

Good host-local config:

```text
POSTGRES_HOST=localhost
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672
```

The intuition:

- from your laptop to Docker-published DB: use localhost
- from one container to another container: use service name

Good infra config also validates itself at startup.

Example checks:

- is PORT a real port?
- is JWT_SECRET still the default?
- is ENCRYPTION_KEY the right length?
- is DATABASE_URL present?
- are prod secrets missing?
- is a dev-only bypass turned on in prod?

Bad config causes a huge amount of production failures. Many outages are not code bugs. They are wrong config, missing config, stale config, or config meant for the wrong environment.


=========================== PACKAGES: WHAT THEY ARE ===========================

A package is reusable software installed into your project or machine.

Examples:

- Python package: `fastapi`, `requests`, `pytest`
- JavaScript package: `react`, `vite`, `typescript`
- Go module: `github.com/go-chi/chi/v5`
- OS package: `nginx`, `curl`, `postgresql-client`
- Docker image package-like artifact: `postgres:15-alpine`, `redis:7-alpine`

Packages are how software reuses other software.

Instead of writing an HTTP router yourself, you install one.
Instead of writing a database driver yourself, you install one.
Instead of writing a test runner yourself, you install one.

Package manager examples:

- Python: `pip`, `uv`, `poetry`
- JavaScript: `npm`, `pnpm`, `yarn`, `bun`
- Go: `go mod`
- Linux Debian/Ubuntu: `apt`
- RHEL/Fedora: `dnf` or `yum`
- macOS: `brew`
- Containers: Docker pulls images from registries

Lockfiles matter because they record exact versions.

Examples:

- `package-lock.json`
- `pnpm-lock.yaml`
- `poetry.lock`
- `requirements.txt` if pinned
- `go.sum`

Without lockfiles, two machines may install different versions and get different behavior.

Big infra rule:

Do not randomly update packages in prod without knowing what changes.

Package updates can include:

- security fixes
- bug fixes
- breaking changes
- removed behavior
- new default settings
- changed dependencies
- performance changes

That is why "just press OK" on software updates is not how production systems are managed.


=========================== WHY NOT JUST PRESS OK ON UPDATES ===========================

On your personal laptop, pressing OK on updates is usually fine.

In production, an update can break real systems.

Examples:

- database version changes query behavior
- Python package changes a function name
- Docker image tag `latest` moves to a new version
- Linux package update restarts a service
- OpenSSL update changes TLS behavior
- Node version update breaks frontend build
- Postgres major version needs data upgrade
- browser automation dependency changes selectors or sandbox behavior

Production updates need a controlled flow:

1. read release notes for major updates
2. update in dev
3. run tests
4. update staging
5. run smoke tests
6. check logs and metrics
7. deploy to prod
8. watch health
9. rollback if bad

There are different kinds of updates:

Patch update:

```text
1.2.3 -> 1.2.4
```

Usually bug/security fixes. Lower risk, but still test.

Minor update:

```text
1.2.3 -> 1.3.0
```

Usually new features. Medium risk.

Major update:

```text
1.2.3 -> 2.0.0
```

May include breaking changes. Higher risk.

Security updates are special. You often need to move faster, but still verify. The mature pattern is not "never update." It is "update through a safe path."

Safe update script thinking:

```text
preflight:
  current version?
  target version?
  backup exists?
  staging tested?

execute:
  install/update package
  restart service if needed

verify:
  service health
  logs clean
  endpoint works
  version now correct

rollback:
  reinstall old version or redeploy old image
```


=========================== BOOTSTRAP: WHAT IT MEANS ===========================

Bootstrap means bring a system from empty or fresh state into a usable baseline.

In normal words:

Bootstrap is the "set this machine/project up from zero" script.

Bootstrap scripts often do:

- install OS packages
- install language runtimes
- install Docker
- create app user
- create directories
- set file permissions
- create `.env` from `.env.example`
- install project dependencies
- create Docker networks or volumes
- start basic services
- run initial migrations
- seed test data

Example names:

```text
bootstrap-dev-machine.sh
setup-server.sh
install-docker.sh
create-app-user.sh
setup-dev.sh
```

Bootstrap is not the same as deploy.

Bootstrap prepares the ground.
Deploy puts a specific app version onto that ground.

Example:

```text
bootstrap:
  install Docker
  install nginx
  create app user
  create /opt/myapp

deploy:
  pull app image version abc123
  run migrations
  restart app
  health check
```

Bootstrap usually happens rarely.
Deploy happens often.


=========================== MIGRATIONS: WHAT THEY ARE ===========================

Migration usually means a controlled change to persistent data structure.

Most commonly, database migration.

Example:

Your app starts with a users table:

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT NOT NULL
);
```

Later you need to add phone numbers:

```sql
ALTER TABLE users ADD COLUMN phone_number TEXT;
```

That `ALTER TABLE` is a migration.

Migrations are needed because production databases already have real data. You cannot just delete the database and recreate it.

Common migration actions:

- create table
- add column
- rename column
- add index
- add unique constraint
- change column type
- split one table into two tables
- backfill missing values
- add foreign key
- add row-level security policies

Migration files are usually numbered:

```text
001_create_users.sql
002_add_orders.sql
003_add_watchlist_market_metadata.sql
004_add_inventory_market_metadata.sql
```

The order matters because later migrations depend on earlier ones.

Migration vs seed:

Migration changes structure.
Seed inserts starting data.

Migration:

```sql
CREATE TABLE cards (...);
```

Seed:

```sql
INSERT INTO cards (name) VALUES ('Radiant Charizard');
```

Migration vs backfill:

Migration adds the new column.
Backfill fills old rows with values.

Example:

```sql
ALTER TABLE watchlists ADD COLUMN external_card_id TEXT;
```

Then a backfill might populate old watchlists:

```sql
UPDATE watchlists
SET external_card_id = ...
WHERE external_card_id IS NULL;
```

Why migrations are dangerous:

- they touch real data
- some lock tables
- some take a long time
- some cannot easily roll back
- failed migrations can leave the DB halfway changed
- app code and database schema must match

Safe migration order:

1. backup database
2. check current migration version
3. run migration in staging
4. test app in staging
5. run migration in prod during safe window
6. verify schema
7. verify app health
8. verify important queries
9. keep rollback or recovery plan

Big tech migration pattern:

Use expand and contract.

Expand:

- add new column/table without breaking old code
- deploy code that writes both old and new shape
- backfill data
- verify

Contract:

- switch reads to new shape
- stop writing old shape
- later remove old column/table

This avoids one huge risky change.


=========================== DEPLOYING: WHAT IT REALLY MEANS ===========================

Deploying means taking a known version of code/config and making it run in an environment.

A serious deploy includes:

- source commit selected
- tests passed
- app built
- artifact created
- Docker image tagged
- image pushed or artifact uploaded
- config loaded
- migrations handled
- service restarted or rolled out
- health check passed
- logs checked
- metrics watched
- rollback available

Common deploy flow:

```text
code -> build -> test -> package -> deploy -> verify -> monitor -> rollback if bad
```

Build means turn source code into something runnable.

Examples:

- compile Go binary
- build React static assets
- install Python dependencies into image
- create Docker image

Package means bundle the runnable thing.

Examples:

- Docker image
- zip file
- tarball
- Go binary
- container image tag

Artifact means the exact thing produced by build/package.

Examples:

```text
pokemontool-server:2026-05-28-a1b2c3
gateway-linux-amd64
web-dist.tar.gz
```

Rollout means gradually putting the new version into service.

Common rollout styles:

- restart all at once
- rolling update
- blue/green deploy
- canary deploy

All-at-once restart:

```text
stop old version -> start new version
```

Simple, but if new version is bad, everyone is affected.

Rolling update:

```text
replace one instance at a time
```

Safer when you have multiple instances.

Blue/green:

```text
blue = current prod
green = new prod candidate
switch traffic when green passes checks
```

Canary:

```text
send 1% of traffic to new version
watch metrics
increase to 10%, 50%, 100%
```

Big tech uses rolling, blue/green, and canary because one bad deploy should not take down everyone.


=========================== THE ORDER INFRA ENGINEERS THINK IN ===========================

This is a practical order from zero to production:

1. Understand the app
2. Identify services
3. Identify dependencies
4. Define config
5. Define secrets
6. Bootstrap machine or platform
7. Provision infrastructure
8. Build artifact
9. Run tests
10. Run security checks
11. Run migrations
12. Deploy app
13. Health check app
14. Smoke test user paths
15. Check logs
16. Check metrics
17. Enable alerts
18. Confirm backups
19. Document rollback
20. Monitor after release

For daily work, the shorter loop is:

```text
change -> test -> build -> deploy -> verify -> watch
```

For emergency work, the loop is:

```text
detect -> assess -> mitigate -> verify -> communicate -> follow up
```

For new server setup, the loop is:

```text
bootstrap -> configure -> secure -> deploy -> monitor -> backup
```


=========================== SCRIPT CATEGORY 1: BOOTSTRAP / SETUP ===========================

Bootstrap/setup scripts prepare a machine, repo, or environment so work can begin.

They answer:

- is the machine ready?
- are required packages installed?
- are directories present?
- are users created?
- are permissions correct?
- are config files present?
- can the app run?

Common tasks:

- install packages
- create users/groups
- create directories
- set permissions
- install Docker
- install language runtimes
- create `.env`
- create local volumes
- verify command availability

Example script names:

```text
setup-server.sh
install-docker.sh
create-app-user.sh
bootstrap-dev-machine.sh
setup-dev.sh
```

What to consider:

- never assume root unless required
- check if something already exists before creating it
- make it idempotent, meaning safe to run multiple times
- print what changed
- fail clearly if a required dependency is missing

Example intuition:

Bad setup script:

```bash
mkdir /opt/app
useradd app
apt install docker
```

Better setup script:

```bash
test -d /opt/app || sudo mkdir -p /opt/app
id app >/dev/null 2>&1 || sudo useradd --system app
command -v docker >/dev/null || echo "Docker missing"
```


=========================== SCRIPT CATEGORY 2: DEPLOY ===========================

Deploy scripts put a specific app version into an environment.

They answer:

- what version am I deploying?
- where am I deploying it?
- has it passed tests?
- do migrations need to run?
- how do I restart or roll out?
- how do I verify?
- how do I rollback?

Common tasks:

- pull image or artifact
- load env vars
- run migrations
- restart service
- wait for health check
- print logs if failed

Example script names:

```text
deploy.sh
deploy-staging.sh
deploy-prod.sh
rollback.sh
```

Good deploy scripts should not just run `docker compose up`.

They should do:

```text
preflight:
  check env
  check ports
  check disk
  check database reachable

execute:
  pull/build image
  run migrations
  restart service

verify:
  health endpoint
  smoke test
  logs

rollback:
  previous image tag
  previous config
```


=========================== SCRIPT CATEGORY 3: HEALTH CHECK / SMOKE TEST ===========================

Health check scripts prove a system is alive.

Smoke test scripts prove the most important user path works.

Health check asks:

```text
Is the service up?
```

Smoke test asks:

```text
Can the app do the most basic useful thing?
```

Common health checks:

- HTTP endpoint returns 200
- DB connection works
- Redis responds
- queue responds
- disk is not full
- process is running
- container is healthy

Example names:

```text
health-check.sh
smoke-test.sh
dependency-check.sh
readiness-check.sh
```

Readiness vs liveness:

Liveness means the process is alive.
Readiness means the process is ready to serve real traffic.

An app can be alive but not ready.

Example:

```text
app process is running
but database connection is broken
```

That is alive, not ready.


=========================== SCRIPT CATEGORY 4: BACKUP / RESTORE ===========================

Backup scripts copy important data somewhere safe.

Restore scripts prove you can bring data back.

Backups without restore tests are hope, not reliability.

Common backup targets:

- Postgres database
- uploaded files
- Docker volumes
- config files
- secrets metadata, not raw secrets in git

Common tasks:

- dump Postgres
- compress backup
- upload to storage
- rotate old backups
- verify backup file exists
- restore into staging
- run row count checks

Example names:

```text
backup-postgres.sh
restore-postgres.sh
backup-volume.sh
backup-retention.sh
postgres_backup_drill.sh
```

Backup concepts:

RPO means Recovery Point Objective.
It answers: how much data can we afford to lose?

Example:

```text
If backups run every 24 hours, worst case you lose almost 24 hours of data.
```

RTO means Recovery Time Objective.
It answers: how long can we be down while recovering?

Example:

```text
If restore takes 2 hours, your RTO is at least 2 hours.
```


=========================== SCRIPT CATEGORY 5: MIGRATION ===========================

Migration scripts apply database changes in a controlled way.

They answer:

- what migration version is the database on?
- which migrations are pending?
- can they run safely?
- did they run successfully?
- do important tables still exist?
- do expected columns exist?

Common tasks:

- apply DB migrations
- check migration status
- backfill data
- verify row counts
- rollback if supported

Example names:

```text
migrate.sh
migration-status.sh
backfill-users.py
verify-migration.sql
```

Important:

Docker init scripts usually only run when the database volume is first created. They do not automatically apply new migrations to an existing production database. That is why real systems need explicit migration runners.


=========================== SCRIPT CATEGORY 6: LOGS / INCIDENT SNAPSHOT ===========================

Log scripts help you see what happened.

Incident snapshot scripts collect evidence during a problem.

Common tasks:

- tail service logs
- search errors
- summarize failures
- collect container status
- collect disk/memory/CPU info
- collect recent deploy version
- collect database health
- collect queue depth

Example names:

```text
logs.sh
grep-errors.sh
incident-snapshot.sh
collect-debug-bundle.sh
service_report.py
infra_report.sh
```

During an incident, do not randomly change things first. Capture state first if possible.

Good incident order:

1. what is broken?
2. who is affected?
3. when did it start?
4. what changed recently?
5. what do logs say?
6. what do metrics say?
7. what is the safest mitigation?
8. how do we verify recovery?


=========================== SCRIPT CATEGORY 7: MONITORING / ALERTING ===========================

Monitoring watches the system.
Alerting tells a human when something needs action.

Monitoring without alerts means nobody may notice.
Alerts without good thresholds create noise.

Common checks:

- disk threshold
- cert expiration
- queue depth
- API latency
- error rate
- memory usage
- CPU usage
- container restarts
- failed jobs
- backup age

Example names:

```text
check-disk.sh
check-cert-expiry.sh
check-queue-depth.py
alert-webhook.sh
health-dashboard.py
```

Metrics examples:

- request count
- request latency
- error count
- CPU percent
- memory bytes
- queue messages ready
- DB connections
- cache hit rate

Logs tell you what happened.
Metrics tell you how much and how often.
Traces tell you where a request went.

Big tech usually thinks in the three pillars:

- logs
- metrics
- traces


=========================== SCRIPT CATEGORY 8: SECURITY ===========================

Security scripts reduce the chance of leaks, abuse, and bad access.

Common tasks:

- scan for secrets
- check open ports
- audit SSH config
- verify file permissions
- rotate keys/tokens
- check dependency vulnerabilities
- verify TLS certs
- check that admin endpoints are not public

Example names:

```text
secrets-scan.sh
open-port-audit.sh
ssh-hardening.sh
permission-audit.sh
rotate-secret.sh
```

Security intuition:

- secrets should not be in git
- databases should not be public by accident
- admin tools should not be exposed to the internet
- prod credentials should be separate from dev credentials
- every external webhook should be verified
- every user input should be validated
- every privileged action should be logged

Least privilege means give each user/service only the access it needs.

Example:

The frontend does not need the database password.
The API server may need database access.
The CI job may need deploy access, but not personal laptop secrets.


=========================== SCRIPT CATEGORY 9: DOCKER / CONTAINER ===========================

Docker scripts manage containers and compose stacks.

Common tasks:

- compose up/down
- rebuild service
- inspect container health
- run one-off command inside container
- check exposed ports
- clean unused images safely
- print service logs

Example names:

```text
compose-up.sh
compose-down.sh
rebuild-service.sh
container-health.sh
docker-clean-safe.sh
```

Docker concepts:

Image:

```text
template for a container
```

Container:

```text
running instance of an image
```

Volume:

```text
persistent storage managed by Docker
```

Network:

```text
private network where containers can reach each other by service name
```

Compose:

```text
file that describes multiple services and how they connect
```

Important Docker rule:

Inside a container, `127.0.0.1` means that same container.
To reach another container, use the Compose service name.


=========================== SCRIPT CATEGORY 10: CI/CD ===========================

CI means Continuous Integration.
CD means Continuous Delivery or Continuous Deployment.

CI checks whether a change is safe to merge.
CD moves a checked change toward an environment.

Common CI tasks:

- install dependencies
- run lint
- run tests
- run typecheck
- build app
- scan for secrets
- scan dependencies
- upload artifacts

Common CD tasks:

- build image
- tag image
- push image
- deploy to staging
- run smoke test
- deploy to prod
- verify release

Example names:

```text
ci-test.sh
build-image.sh
tag-release.sh
push-image.sh
release-check.sh
```

CI should be boring and repeatable.

If CI only works on one person's laptop, it is not real CI.

Good CI is split by responsibility:

- frontend job
- backend job
- Python job
- Docker compose config job
- security scan job


=========================== SCRIPT CATEGORY 11: NETWORK ===========================

Network scripts prove services can talk to each other.

Common tasks:

- check ports
- DNS lookup
- TLS certificate test
- ping
- traceroute
- firewall check
- HTTP connectivity check

Example names:

```text
port-check.sh
dns-check.sh
tls-check.sh
firewall-audit.sh
connectivity-check.sh
port_preflight.sh
```

Common network concepts:

Port:

```text
number where a service listens
```

Example:

```text
Postgres = 5432
Redis = 6379
HTTP = 80
HTTPS = 443
```

DNS:

```text
name to address lookup
```

Example:

```text
api.example.com -> 203.0.113.10
```

TLS:

```text
encryption for HTTPS
```

Firewall:

```text
rules deciding what traffic can enter or leave
```

Reverse proxy:

```text
public entrypoint that forwards traffic to internal services
```

Examples:

- Nginx
- Caddy
- Traefik
- Envoy


=========================== SCRIPT CATEGORY 12: PROVISIONING ===========================

Provisioning means creating or preparing infrastructure resources.

Provisioning can mean:

- create VM
- create database
- create network
- create firewall rule
- create load balancer
- create DNS record
- create object storage bucket
- install systemd service
- configure reverse proxy

Example names:

```text
provision-vm.sh
install-systemd-service.sh
setup-nginx.sh
setup-caddy.sh
configure-firewall.sh
```

Provisioning tools:

- Bash scripts
- Terraform
- Pulumi
- Ansible
- CloudFormation
- Kubernetes manifests
- Helm charts

Bash can provision simple things.
Terraform is common for cloud resources.
Ansible is common for configuring servers.
Kubernetes manifests define workloads in clusters.


=========================== MORE SCRIPT TYPES BIG INFRA TEAMS USE ===========================

The earlier list is the core. Big teams also commonly have these.

Capacity scripts:

- check CPU/memory growth
- predict disk full date
- report database size growth
- report queue throughput

Cost scripts:

- report cloud spend
- find unused disks
- find idle load balancers
- find oversized instances

Compliance scripts:

- check encryption enabled
- check audit logs enabled
- check public buckets
- check required tags/owners

Certificate scripts:

- check TLS expiration
- renew certs
- reload proxy after renewal

DNS scripts:

- verify records
- compare expected vs actual DNS
- check propagation

Release scripts:

- generate changelog
- tag release
- create release notes
- promote image from staging to prod

Data repair scripts:

- fix bad rows
- dedupe records
- recalculate derived fields
- repair missed events

Job/queue scripts:

- replay failed jobs
- drain queue
- check dead-letter queue
- measure queue lag

Access scripts:

- create temporary access
- audit users
- remove old users
- rotate SSH keys

Disaster recovery scripts:

- restore database into new environment
- rebuild service from backups
- test failover
- verify runbook steps

Inventory scripts:

- list servers
- list services
- list exposed ports
- list package versions
- list container images

Drift detection scripts:

- compare actual config to expected config
- detect manual changes on servers
- detect untracked cloud resources


=========================== THE MUST-KNOW INFRA SCRIPT STACK ===========================

Learn these first in Bash:

```text
setup
deploy
rollback
health check
backup
restore
migrate
logs
incident snapshot
port preflight
secrets audit
docker compose wrapper
```

Then learn these in Python when parsing, APIs, JSON, or reports get annoying in Bash:

```text
inventory reports
cloud API automation
log parsers
backup verification
health dashboards
queue monitors
config validators
dependency auditors
cost reports
drift detectors
```

Bash is best for:

- running commands
- gluing tools together
- simple checks
- file operations
- service restart scripts

Python is best for:

- JSON parsing
- API calls
- reports
- complex branching
- data validation
- larger automation
- tests around automation logic

SQL is needed for:

- migrations
- data checks
- backfills
- reporting from databases

YAML is needed for:

- Docker Compose
- GitHub Actions
- Kubernetes
- CI/CD config

Terraform/HCL is needed for:

- cloud infrastructure as code
- networks
- VMs
- databases
- buckets
- DNS


=========================== HOW THIS MAP APPLIES TO YOUR REPO ===========================

Your repo already has many of the right learning scripts.

Pokemon scripts to understand:

```text
port_preflight.sh
health-check.sh
infra_report.sh
incident_snapshot.sh
postgres_backup_drill.sh
service_report.py
queue_report.py
db_report.py
pokemon_runtime_dependency_auditor.py
pokevend_config_validator.py
```

How to think about them:

`port_preflight.sh` checks whether ports are free before Docker tries to bind them.

`health-check.sh` proves services are alive.

`infra_report.sh` gives a snapshot of the system.

`incident_snapshot.sh` captures state when something is wrong.

`postgres_backup_drill.sh` practices backup and restore thinking.

`service_report.py` summarizes service status.

`queue_report.py` checks RabbitMQ/queue behavior.

`db_report.py` checks database state.

`pokemon_runtime_dependency_auditor.py` maps what services exist, what depends on what, and what can break.

`pokevend_config_validator.py` should make sure config is valid before runtime.

The best order to master your repo infra:

1. Read `Pokemon/docker-compose.yml`.
2. Learn what each service does.
3. Learn which ports each service uses.
4. Learn which services are private vs public.
5. Run config validation before startup.
6. Run port preflight before startup.
7. Start only core services first.
8. Run health checks.
9. Run smoke tests.
10. Check logs.
11. Check DB tables.
12. Check RabbitMQ queues.
13. Practice backup.
14. Practice restore.
15. Practice migration.
16. Practice incident snapshot.

The core Pokemon runtime shape:

```text
client -> Go server -> Postgres
client -> Go server -> Redis
api-consumer -> RabbitMQ -> Go worker -> Postgres -> SSE -> client
Go server -> PokeTCG -> market data
```

If you understand that flow, most infra debugging becomes less mysterious.


=========================== BIG TECH INFRA MODEL IN PLAIN ENGLISH ===========================

Big tech does not have one magic model everyone uses, but most mature systems rhyme.

The common model is:

```text
source control
  -> CI
  -> artifact
  -> environment config
  -> deploy system
  -> health checks
  -> monitoring
  -> incident response
  -> postmortem
```

Source control:

```text
Git stores the code and review history.
```

CI:

```text
Automatic checks prove a change builds and tests.
```

Artifact:

```text
The exact thing to deploy, usually a Docker image.
```

Environment config:

```text
Dev/staging/prod values are injected without changing code.
```

Deploy system:

```text
Rolls out the artifact.
```

Health checks:

```text
Prove the service is alive and ready.
```

Monitoring:

```text
Watches metrics, logs, traces, jobs, queues, and dependencies.
```

Incident response:

```text
Humans follow a process when something is broken.
```

Postmortem:

```text
Incident learning document. Not blame. Cause, impact, response, prevention.
```

Big tech also cares about:

- SLOs: service level objectives
- SLIs: service level indicators
- error budgets
- change management
- blast radius
- rollback safety
- least privilege
- audit logs
- capacity planning
- disaster recovery

SLI:

```text
What we measure.
Example: 99.9% of requests return under 300ms.
```

SLO:

```text
The target we promise internally.
Example: 99.9% availability.
```

Error budget:

```text
How much failure is acceptable before we slow down risky changes.
```

Blast radius:

```text
How much damage one failure can cause.
```

Rollback:

```text
Return to the previous known good version.
```

Runbook:

```text
Step-by-step instructions for operating or fixing something.
```

Postmortem:

```text
Incident learning document. Not blame. Cause, impact, response, prevention.
```


=========================== FINAL INFRA INTUITION ===========================

Infrastructure engineering is mostly about turning scary manual operations into repeatable systems.

A beginner thinks:

```text
How do I start the app?
```

An infra engineer thinks:

```text
How does anyone start the app safely from a clean machine?
How does it know its config is valid?
How does it deploy?
How does it fail?
How do we know it failed?
How do we recover data?
How do we roll back?
How do we avoid the same incident twice?
```

That is the level-up.

The scripts are not random. They form a safety chain:

```text
bootstrap -> configure -> build -> test -> migrate -> deploy -> verify -> monitor -> backup -> recover
```

When you hear infra people talk, map every word back to that chain.


Start plane :
    /home/iscjmz/ops/plane-selfhost/plane.sh start

  Starts Plane in Docker. It brings up Plane’s containers: frontend, API, worker,
  scheduler, realtime server, Postgres, Redis/Valkey, RabbitMQ, MinIO, and proxy. After
  this, Plane is available at:

  http://localhost:8095

  /home/iscjmz/ops/plane-selfhost/plane.sh status

  Shows whether Plane containers are running, stopped, healthy, or exited.

  /home/iscjmz/ops/plane-selfhost/plane.sh logs api

  Shows live logs for the Plane API container. Use this when Plane loads weird, login
  fails, or the backend errors.

  /home/iscjmz/ops/plane-selfhost/plane.sh stop 

  Stops Plane containers. It does not delete Plane’s database/files. Your data stays in
  Docker volumes.

  /home/iscjmz/ops/plane-selfhost/plane.sh backup

  Runs Plane’s backup action for its local data: Postgres data, uploads/MinIO, RabbitMQ
  data, Redis data. Backups go under the Plane install folder.


=========================== VISIBLE CHECK 2026-07-07 ====================================
If you can see this, you are looking at the saved file on disk: /home/iscjmz/shopify/shopify/Explanations_TO_EVERYTHING.md
The big infrastructure section starts above at WHOLE PROJECT INFRASTRUCTURE MAP.

=========================== BOTTOM PROJECT INFRASTRUCTURE GUIDE ===========================
This is the bottom copy. If Ctrl+F finds this heading, you are seeing the saved file.

BIG PICTURE
This repo is a local business platform made of multiple Docker Compose stacks plus a few host tools.
The main stacks are:

1. PokemonTool
   Path: /home/iscjmz/shopify/shopify/Pokemon
   Purpose: Pokemon card market intelligence, watchlists, alerts, inventory, slabs, eBay/TCG data, dashboard.

2. Odoo
   Path: /home/iscjmz/shopify/shopify/odoo
   Compose: /home/iscjmz/shopify/shopify/docker-compose.odoo.yml
   Purpose: storefront/ERP/business workflows.

3. NexusOS / Shopify platform
   Path: /home/iscjmz/shopify/shopify
   Compose: docker-compose.yml + docker-compose.dev.yml + docker-compose.universe.yml
   Purpose: broader Shopify platform with web UI, Go gateway, Python AI service, Kafka, Qdrant, Ollama, Temporal.

4. Plane
   Path: /home/iscjmz/ops/plane-selfhost
   Script: /home/iscjmz/ops/plane-selfhost/plane.sh
   Purpose: project management, issues, sprint planning, deliverables.

5. Understand Anything
   Path: /home/iscjmz/shopify/shopify/Pokemon/.understand-anything
   Purpose: generated code-understanding/knowledge graph data. It is tooling, not a runtime service.

LOCAL VS CONTAINER
Local means everything uses your computer's CPU/RAM/disk.
Container means Docker isolates the service, but it still runs on your computer.

Host processes examples:
- VS Code
- Codex
- terminal
- go run main.go when you run Go directly
- uvicorn when you run Python directly

Container examples:
- Postgres
- Redis
- RabbitMQ
- Kafka
- Qdrant
- Odoo
- Grafana
- Pokemon server/client if started with Docker Compose

DOCKER DNS
Docker Compose creates a private Docker network.
Every service name becomes a DNS name inside that network.

In Pokemon/docker-compose.yml:
- postgres becomes DNS name postgres
- redis becomes DNS name redis
- rabbitmq becomes DNS name rabbitmq
- server becomes DNS name server
- api-consumer becomes DNS name api-consumer
- poketcg becomes DNS name poketcg

Inside containers, use service names:
- postgres:5432
- redis:6379
- rabbitmq:5672
- http://server:3001
- http://api-consumer:8001
- http://poketcg:8765

From your laptop/browser, use localhost ports:
- Pokemon UI: http://127.0.0.1:5173
- Pokemon API: http://127.0.0.1:3001
- Odoo: http://127.0.0.1:8069
- Nexus web: http://127.0.0.1:3000
- Nexus gateway: http://127.0.0.1:8080
- Nexus AI: http://127.0.0.1:8000

POKEMONTOOL STACK
Main file: /home/iscjmz/shopify/shopify/Pokemon/docker-compose.yml

postgres:
- Container: pokemontool_postgres
- Source of truth for users, cards, watchlists, alerts, inventory, shows, prices, listings, deals.
- Data persists in Docker volume pokevend_pgdata.
- Migrations live in Pokemon/database/migrations.

redis:
- Container: pokemontool_redis
- Cache for repeated reads like search/trending/deal data.
- Redis does not talk directly to Postgres. The Go server talks to both.

rabbitmq:
- Container: pokemontool_rabbitmq
- Internal message bus.
- api-consumer/scraper publish messages.
- Go server worker consumes messages.

poketcg:
- Container: pokemontool_poketcg
- Local Pokemon card lookup/pricing API.
- Other containers call http://poketcg:8765.

server:
- Container: pokemontool_server
- Path: Pokemon/server
- Language: Go
- Entry point: server/main.go
- Purpose: main API, auth, routes, business logic, Postgres access, Redis cache, RabbitMQ worker, SSE notifications.
- Depends on postgres, redis, rabbitmq, poketcg, and optionally Odoo.

client:
- Container: pokemontool_client
- Path: Pokemon/client
- React + Vite UI.
- Browser opens this at port 5173.

api-consumer:
- Container: pokemontool_api_consumer
- Path: Pokemon/services/api-consumer
- Python/FastAPI.
- Handles eBay, TCGplayer, seller hub, sold comps, slab parsing.
- Talks to Postgres and RabbitMQ.

analytics-engine:
- Container: pokemontool_analytics
- Path: Pokemon/services/analytics-engine
- Python analytics jobs for trends, opportunities, deals, news.
- Talks to Postgres and RabbitMQ.

scraping-service:
- Container: pokemontool_scraper
- Path: Pokemon/services/scraping-service
- Go + Playwright.
- Optional browser scraping for Facebook/Mercari.
- Heavier service; usually only start when needed.

observability:
- loki stores logs.
- promtail ships Docker logs to Loki.
- grafana visualizes logs/metrics.
- prometheus scrapes metrics.

POKEMON REQUEST FLOW
Browser -> Pokemon client -> Go server -> handler -> service -> store -> Postgres.

Cache flow:
1. Browser searches for a card.
2. Go service checks Redis.
3. If cache hit, return cached JSON.
4. If cache miss, query Postgres through store layer.
5. Save result to Redis with TTL.
6. Return response to browser.

Queue flow:
1. api-consumer/scraper finds listing or market event.
2. It publishes to RabbitMQ.
3. Go worker consumes RabbitMQ message.
4. Worker writes alerts/listings/snapshots into Postgres.
5. Server pushes live updates to browser through SSE.

POKEMON DIRECTORY MAP
Pokemon/client:
- React frontend.
- src/pages: screens.
- src/components: reusable UI pieces.
- src/services/api.js: frontend API calls.
- src/store: Redux/client state.

Pokemon/server:
- main.go: orchestrator/wiring.
- config/: env config plus DB/Redis/RabbitMQ clients.
- routes/: URL mapping.
- handlers/: HTTP request/response layer.
- services/: business logic.
- store/: SQL/repository layer.
- models/: Go structs.
- middleware/: auth/rate limit/request middleware.
- worker/: background queue consumers.
- pkg/: helpers.

Pokemon/services/api-consumer:
- main.py: FastAPI orchestrator.
- services/: eBay/TCG/seller/sold-comps logic.
- repositories/: Postgres access.
- publisher/: RabbitMQ publisher.
- tests/: Python tests.

Pokemon/services/analytics-engine:
- analyzers/: trend/deal/opportunity logic.
- repositories/: Postgres access.
- models/: schemas.
- tests/: analytics tests.

Pokemon/services/scraping-service:
- scraper/: site scraping logic.
- publisher/: RabbitMQ publisher.

Pokemon/database:
- migrations/: schema changes.
- seeds/: starter data.

Pokemon/scripts:
- dev-startup.sh: mixed local dev startup with Docker infra + host Go/Python.
- setup-dev.sh: install/setup local dev pieces.
- health-check.sh: checks runtime health.
- docker_health-check.sh: Docker-specific health checks.
- docker_check.sh: counts running containers.
- postgres_backup_drill.sh: backup/list/verify/restore Postgres dumps.
- service_report.py: service state report.
- queue_report.py: RabbitMQ queue health/report.
- db_report.py: Postgres report.
- pokemon_runtime_dependency_auditor.py: maps services, ports, health, dependencies, blast radius.
- display.sh: interactive CLI practice script.

ODOO STACK
Compose: /home/iscjmz/shopify/shopify/docker-compose.odoo.yml

odoo-db:
- Container: shopify-odoo-db
- Postgres for Odoo only.

odoo:
- Container: shopify-odoo
- Image: odoo:19.0
- Uses odoo/config/odoo.conf.
- Loads custom addons from odoo/custom_addons.
- Exposed at http://127.0.0.1:8069.
- Joins network pokemon-odoo-bridge so Pokemon server can call it.

Odoo app files:
- odoo/custom_addons/pokecard_storefront/__manifest__.py: addon metadata.
- controllers/: HTTP routes.
- models/: Odoo data models.
- views/: XML pages/admin views.
- scripts/sync_pokemon_inventory_to_odoo.py: sync utility.

Odoo flow:
Browser -> Odoo storefront -> Odoo app -> Odoo Postgres.
Pokemon server -> shopify-odoo:8069 over pokemon-odoo-bridge.

NEXUSOS STACK
Main compose: /home/iscjmz/shopify/shopify/docker-compose.yml
Dev compose: /home/iscjmz/shopify/shopify/docker-compose.dev.yml
Universe ports: /home/iscjmz/shopify/shopify/docker-compose.universe.yml

postgres:
- Container: nexusos-postgres
- pgvector Postgres for relational/vector data.

redis:
- Container: nexusos-redis
- cache/session/idempotency runtime state.

qdrant:
- Container: nexusos-qdrant
- vector DB for RAG/search/memory.

zookeeper + kafka:
- Containers: nexusos-zookeeper, nexusos-kafka
- event streaming/webhook buffering.

ollama:
- Container: nexusos-ollama
- local LLM runtime.

temporal + temporal-ui:
- Containers: nexusos-temporal, nexusos-temporal-ui
- long-running workflow engine and UI.

gateway:
- Path: services/gateway
- Go API service.
- Depends on Postgres, Redis, Kafka.

ai:
- Path: services/ai
- Python/FastAPI AI service.
- Depends on Qdrant, Kafka, Ollama.

web:
- Path: apps/web
- Frontend.
- Depends on gateway.

Nexus flow:
Browser -> web -> gateway -> Postgres/Redis/Kafka -> ai when needed -> Qdrant/Ollama/Kafka.

PLANE
Path: /home/iscjmz/ops/plane-selfhost
Script: /home/iscjmz/ops/plane-selfhost/plane.sh

Commands:
- plane.sh start: starts Plane containers.
- plane.sh status: shows state.
- plane.sh logs api: API logs.
- plane.sh stop: stops Plane without deleting data.
- plane.sh backup: backs up Plane local data.

Plane is not user traffic for Pokemon. It is project management:
- backlog
- bugs
- sprint board
- deliverables
- release tracking

STARTUP OPTIONS
Card-store only:
cd /home/iscjmz/shopify/shopify
scripts/dev-cardstore.sh up

This starts:
1. pokemon-odoo-bridge network.
2. Odoo.
3. PokemonTool.
4. Leaves optional scraping off unless requested.

Full universe:
cd /home/iscjmz/shopify/shopify
scripts/dev-universe.sh up

This starts:
1. Odoo.
2. NexusOS.
3. PokemonTool.
4. Shared bridge network.

Pokemon only:
cd /home/iscjmz/shopify/shopify/Pokemon
docker compose -f docker-compose.yml -f docker-compose.local-no-postgres-port.yml up -d --build

Stop all Docker containers globally:
docker stop $(docker ps -q)

Stop card-store:
cd /home/iscjmz/shopify/shopify
scripts/dev-cardstore.sh down

Stop full universe:
cd /home/iscjmz/shopify/shopify
scripts/dev-universe.sh down

Stop Pokemon only:
cd /home/iscjmz/shopify/shopify/Pokemon
docker compose down

DEPENDENCY GRAPH
- Plane: separate project management stack.
- Odoo: odoo -> odoo-db.
- NexusOS: web -> gateway -> postgres/redis/kafka -> zookeeper.
- NexusOS AI: ai -> qdrant/kafka/ollama.
- Temporal UI -> temporal -> postgres.
- Pokemon client -> Pokemon server.
- Pokemon server -> postgres/redis/rabbitmq/poketcg/odoo.
- Pokemon api-consumer -> postgres/rabbitmq/server.
- Pokemon analytics -> postgres/rabbitmq.
- Pokemon scraper -> rabbitmq.
- Observability: promtail -> Docker logs -> loki -> grafana; prometheus -> metrics.

CI/CD
CI means prove code before merge.
CD means ship code after merge.

Pokemon CI file:
/home/iscjmz/shopify/shopify/Pokemon/.github/workflows/ci.yml

It does:
- Go build/vet/test for server.
- Go build for scraper.
- Python ruff/mypy for api-consumer and analytics-engine.
- SQL migration/seed validation against real Postgres service container.

Pokemon deploy file:
/home/iscjmz/shopify/shopify/Pokemon/.github/workflows/deploy.yml

It does:
1. Runs on main or manual trigger.
2. SSHes into EC2.
3. cd /opt/pokemontool.
4. git pull origin main.
5. applies migrations.
6. docker compose up -d --build.
7. curls health endpoint until healthy.

PRODUCTION WORKFLOW
1. Create Plane ticket.
2. Define acceptance criteria.
3. Create branch like feat/card-price-alerts.
4. Make focused code changes.
5. Add/update tests.
6. Run local health checks.
7. Commit with conventional commit.
8. Push branch.
9. Open PR.
10. CI must pass.
11. Review security/config/migration impact.
12. Merge to main.
13. Deploy workflow runs.
14. Verify health, logs, and user path.
15. Close Plane ticket with PR/deploy link.

Good commit examples:
- feat: add seller hub batch ingestion
- fix: handle redis cache miss without failing search
- test: cover slab opportunity scoring
- docs: document local universe startup
- chore: add compose health checks

Definition of done:
- code merged
- CI green
- tests prove behavior
- docs/scripts updated if workflow changed
- health check passes after deploy
- rollback path known

PRODUCTION HARDENING ROADMAP
- Do not commit secrets.
- Use GitHub/AWS secrets.
- Add staging before production.
- Use tagged Docker images instead of rebuilding random latest on EC2.
- Use real migration version tracking.
- Backup before deploy.
- Add rollback script.
- Add uptime checks/alerts.
- Add npm audit/govulncheck/pip-audit/secret scan.
- Add e2e smoke tests for Pokemon dashboard, Odoo storefront, and critical API flows.

DEBUGGING METHOD
1. Identify the broken surface: browser, API, DB, queue, cache, AI, logs.
2. Find owning service in compose.
3. Check container state: docker compose ps.
4. Read one service log: docker compose logs -f --tail=100 server.
5. Hit health endpoint.
6. Follow code path: route -> handler -> service -> store/repository -> database/queue/cache.
7. Search env/config names:
   rg "POSTGRES_HOST|REDIS_URL|RABBITMQ_URL|DATABASE_URL|QDRANT_URL|GO_INTERNAL_URL"
8. Fix the smallest thing.
9. Prove with test, curl, health check, or UI path.

MENTAL MODEL
Compose files define what exists.
Environment variables define how services find each other.
Docker networks provide DNS names.
Entry points start services.
Handlers/controllers receive requests.
Services hold business logic.
Stores/repositories touch databases.
Queues decouple background work.
Caches speed up repeated reads.
Health checks prove life.
CI proves code before merge.
CD ships proven code.
Plane tracks work.
Docs preserve knowledge.
