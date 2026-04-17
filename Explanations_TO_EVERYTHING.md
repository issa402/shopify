====================RABBITMQ_PUBLISHER================================
Rabbitmq_publisher : So we use a TCP connection to RabbitMQ broker. Create channels which don not create a new TCP connection. THE RABIITMQ FILE CONTAIN THE ETHODS FOR THE SERVICE FILES (EBAY AND TCG). EVERYHTING INITILAIZED IN RABBITMQ IS CALLED IN MAIN(THE ORCHESTRATOR AND ONCE MAIN CREATES A RABBITMQ PUBLISHER IT THEN PASSES INTO EBAY SERVICES AND TCG SERVICES IN THEIR RESPECTED INIT FUNCTIONS. FROM THERE INSIDE THOSE SERVICE FILES THEY CALL METHODS FROM rabbitmqpublisher SUCH AS **await self.publisher.publish("listings", payload)** USED FOR SINGLTETON USE THATS WHY GLOBAL IS CALLED **global publisher, ebay_svc, tcg_svc** AND HERE PUBLISHER IS INITIALIZED **publisher = RabbitMQPublisher(rabbitmq_url)** THEN PASSED TO THE SERVICE LAYER **ebay_svc = EbayService(repo=EbayRepo(), publisher=publisher) tcg_svc = TCGService(repo=TCGRepo(), publisher=publisher)**.


queue_report.py: SCRIPT TO CHECK IF RABBITMQ IS UP AND RUNNING HEALTHY. FIRST CONNECTS TO RABBITAMQP AND RABBITMGMT WHICH IS A MANAGMENT TOOL TO SEE RABBITMQ DIAGNOSTICS BY LOGGING IN WITH USERNAME AND PASSWORD. CLASS QUEUEREPORTER TAKES IN TWO ARGUMENTS WHIHC ARE CONNECTION URLS. ASYNC DEF CHECK CONNECTION CONNETCS TO AMQP. CHECK QUEUES AMQP TAKES IN THE QUEUE NAME WHCIH IS ONLY listing we only have one queue name and that can be confirmed in TCG AND EBAY SERVCIES WHERE THEY APPENDED A LISTING PAYLOAD CALLED LISTINGS. IT CHECKS FOR EACH QNAME. ALSO aio_pika talks to RabbitMq and httpx handles the HTTP requests for the Mnagment Rabbitmq. SO FIRST IT OPENS A CONNECTION THEN A CHANNEL IT ITERATES THROUGH EACH QUEUE NAME IF EXISTS BY using **channel.declare_queue(passive =True)** which means dont touch it just inspect.  the **queue.declarations_result.message_count** checks how many messages are inside the 'listing' queue. The **declaration_result.consumer_count** checks how many messages are sitting in the listings queue. Inside it also chceks if that specific queue names exists if Not rabbitmq kills the channel and onto the next queue and once outer loop existed returns error if couldnt expect queues. The CHECK_MGMT_STATS it first opens a HTTP client . Then hits the the rabbitmq web api  using client.get . Initialzie data to grab all json and then using data.get for the paremeter queue totals and parse the JSN to find the total message count across eveyr queue on the server not just one named listing. Then finally main creates an insnace of the QUEUEReporter and runs the functions inside using await. EVERY PYTHON FILE WILL ALWAYS BE MAIN ITS JUST HOW ETHYRE PORGRAMMED SO IF NAME WILL ALWAYS EQUAL MAIN. **Asyncio.run(main())** means stars the asynchronous event loop to power all await commands



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

==================DOCKER =================================================
docker compose up -d : is to run everything in the docker-compose.yml 
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


**Left Of Migrations File






































    The Handshake: Did the app connect? (The log you found).
    The Delivery: Did a message actually go from A to B?

Here is the best way to handle this using a script:
1. The "Connection" Check (Using your awk idea)
This is perfect for a quick "Is the wire plugged in?" check. You can run this to see only successful logins:
bash

docker compose logs rabbitmq | awk '/authenticated and granted access/'

Use code with caution.
2. The "Better" Way: Check the Queue Stats
Since your worker processes messages so fast that the queue looks empty, the best "proof" is to check the cumulative total of messages that have passed through.
Run this command; it shows how many messages were ever delivered, even if the queue is currently 0:
bash

docker exec pokemontool_rabbitmq rabbitmqctl list_queues name messages_ready messages_delivered_get

Use code with caution.

    messages_ready: Should be 0 (if your worker is fast).
    messages_delivered_get: This number should go up every time your scraper runs. If this is greater than 0, RabbitMQ definitely worked.

3. The "Automated" Health Script
If you want a single script to tell you "Is RabbitMQ working?", create a file called check_rabbit.sh:
bash

#!/bin/bash

echo "--- Checking RabbitMQ Connection ---"
# Check for successful login in the last 50 lines of logs
if docker compose logs rabbitmq --tail 50 | grep -q "granted access"; then
    echo "✅ [SUCCESS] App is authenticated."
else
    echo "❌ [ERROR] No successful logins found recently."
fi

echo "--- Checking Data Flow ---"
# Check if any messages have ever been delivered
DELIVERED=$(docker exec pokemontool_rabbitmq rabbitmqctl list_queues messages_delivered_get --formatter json | grep -o '[0-9]\+')

if [ "$DELIVERED" -gt 0 ]; then
    echo "✅ [SUCCESS] $DELIVERED messages have been processed."
else
    echo "⚠️ [WARNING] No messages have moved through the queue yet."
fi

Use code with caution.
Summary

    Use awk / grep on logs to debug connection issues (bad passwords, wrong ports).
    Use rabbitmqctl to debug data flow issues (messages getting lost or stuck).

Does that sound like what you're looking for, or do you want to auto-trigger an action whenever a new connection is logged?
