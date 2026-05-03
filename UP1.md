# UP1 - Infrastructure, Networking, Firewalls, SSH, IAM

This is the separate mastery file. Your main `Explanations_TO_EVERYTHING.md` was restored.

## The Infra Mindset

Every outage can be walked like a chain:

Client -> DNS -> IP -> Route -> Firewall -> Port -> Process -> Logs -> Identity -> Data

When something breaks, ask:

1. What name is the client using?
2. What IP does that name resolve to?
3. Can the client route to that IP?
4. Is a firewall/security group blocking it?
5. Is the server listening on the expected port?
6. Is the right process behind that port?
7. Do logs show the request?
8. Does the user/service have permission?
9. Is the database/dependency reachable?
10. What changed recently?

## Core Networking

An IP address identifies a machine or network interface.

`127.0.0.1` means this same machine. If you are inside a Docker container, `127.0.0.1` means that container, not your host and not another container.

`0.0.0.0` means all IPv4 interfaces. If a service binds to `0.0.0.0:80`, it is listening on every network interface.

Private IP ranges:

- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`

These are internal/private networks. Public internet traffic usually reaches them through NAT, VPN, tunnels, load balancers, or port forwarding.

## Subnets

CIDR notation looks like this:

```text
192.168.1.0/24
```

The `/24` means the first 24 bits are the network part. A `/24` usually gives 256 addresses: `192.168.1.0` through `192.168.1.255`.

Subnet intuition:

- Bigger slash number = smaller network
- Smaller slash number = bigger network
- `/32` = one exact IP
- `/24` = common LAN-sized network
- `/16` = much bigger
- `/8` = huge

## Must-Know Network Commands

```bash
ip addr
```

Shows network interfaces and IPs.

```bash
ip -br addr
```

Shorter version of `ip addr`.

```bash
ip route
```

Shows where packets go. The `default via` line is your gateway out of the local network.

```bash
ip route get 8.8.8.8
```

Shows the exact route Linux would use to reach `8.8.8.8`.

```bash
dig +short example.com
```

Shows what IP a DNS name resolves to.

```bash
ping 8.8.8.8
```

Tests ICMP reachability. Ping can fail even when HTTP works because ICMP may be blocked.

```bash
nc -vz host port
```

Tests a TCP port.

Open port usually says:

```text
Connection to host port [tcp/*] succeeded!
```

Closed port often says:

```text
Connection refused
```

Firewall/routing problems often cause:

```text
timed out
```

```bash
curl -v http://host:port
```

Debugs HTTP and shows connection details, headers, status codes, and errors.

## Ports

Common ports:

- `22`: SSH
- `53`: DNS
- `80`: HTTP
- `443`: HTTPS
- `5432`: PostgreSQL
- `3306`: MySQL
- `6379`: Redis
- `5672`: RabbitMQ AMQP
- `15672`: RabbitMQ management UI
- `8080`: common dev/proxy port

Use this to see what is listening:

```bash
sudo ss -tulpn
```

Flags:

- `t`: TCP
- `u`: UDP
- `l`: listening
- `p`: process
- `n`: numeric output

Example:

```text
tcp LISTEN 0 4096 127.0.0.1:5432 0.0.0.0:* users:(("postgres",pid=1234,fd=7))
```

Meaning: Postgres is listening on port `5432`, but only locally because it is bound to `127.0.0.1`.

## Firewalls

A firewall decides if packets are allowed.

Firewall rule shape:

```text
allow source -> destination -> protocol -> port
deny source -> destination -> protocol -> port
```

UFW commands:

```bash
sudo ufw status verbose
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow from 203.0.113.10 to any port 22 proto tcp
sudo ufw deny 5432/tcp
sudo ufw status numbered
sudo ufw delete 3
```

Before enabling UFW on a remote server, allow SSH:

```bash
sudo ufw allow OpenSSH
sudo ufw enable
```

Debug unreachable port:

1. Check service:

```bash
sudo ss -tulpn | grep ':PORT'
```

2. Check local connection:

```bash
nc -vz 127.0.0.1 PORT
```

3. Check firewall:

```bash
sudo ufw status verbose
```

4. Check logs:

```bash
journalctl -u service-name -f
```

## SSH

Basic login:

```bash
ssh user@server_ip
```

Custom port:

```bash
ssh -p 2222 user@server_ip
```

Specific key:

```bash
ssh -i ~/.ssh/my_key user@server_ip
```

Verbose debug:

```bash
ssh -vvv user@server_ip
```

Generate a modern SSH key:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

SSH key idea:

- Private key stays on your machine.
- Public key goes on the server in `~/.ssh/authorized_keys`.
- Never share the private key.

Important permissions:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/id_ed25519
```

SSH server config:

```text
/etc/ssh/sshd_config
```

Important settings:

```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

After edits:

```bash
sudo sshd -t
sudo systemctl reload ssh
```

Keep one SSH session open while testing new SSH settings from another terminal.

## Users, Groups, Permissions

```bash
whoami
id
cat /etc/passwd
cat /etc/group
```

Create user:

```bash
sudo adduser devuser
```

Add to sudo:

```bash
sudo usermod -aG sudo devuser
```

Important: `-aG` means append to group. Forgetting `-a` can remove the user from other groups.

Permissions example:

```text
drwxr-x--- 2 issa developers 4096 Apr 30 12:00 app
```

Meaning:

- `d`: directory
- `rwx`: owner can read/write/execute
- `r-x`: group can read/execute
- `---`: others have no access
- `issa`: owner
- `developers`: group

Permission numbers:

- read = `4`
- write = `2`
- execute = `1`
- `7` = read/write/execute
- `6` = read/write
- `5` = read/execute

Examples:

```bash
chmod 755 script.sh
chmod 600 secret.txt
sudo chown user:group file
```

## IAM

IAM means Identity and Access Management.

IAM always asks:

1. Who are you?
2. How do we prove it?
3. What are you allowed to do?
4. On which resource?
5. Under what conditions?
6. How do we audit it?

Important words:

- Principal: user, service, role, machine identity
- Authentication: prove who you are
- Authorization: decide what you can do
- Policy: rule document
- Role: assumable identity
- Group: collection of users
- Resource: thing being accessed
- Action: operation like read/write/delete
- Least privilege: only grant what is needed

Linux IAM:

- users
- groups
- sudo
- file permissions
- service users

Cloud IAM:

- users
- groups
- roles
- policies
- service accounts

Master rule: do not run apps as root, do not give permanent admin by default, do not put secrets in code.

## Docker Networking

Inside Docker Compose, services talk by service name.

Example:

```text
api -> postgres:5432
```

Inside a container, `localhost` means that same container.

Port mapping:

```yaml
ports:
  - "127.0.0.1:5432:5432"
```

Means host `127.0.0.1:5432` forwards to container port `5432`. Only local host can reach it.

```yaml
ports:
  - "5432:5432"
```

Means all host interfaces may expose `5432`. Be careful with databases.

Commands:

```bash
docker compose ps
docker compose logs --tail=100 service
docker network ls
docker network inspect network_name
docker inspect container_name
docker exec -it container_name sh
```

## Nginx Reverse Proxy

Typical path:

```text
Internet -> firewall -> nginx -> backend -> database
```

Nginx commonly:

- listens on `80`/`443`
- terminates TLS
- forwards to backend
- logs requests
- serves static files

Check config:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Debug:

```bash
curl -I http://localhost
curl -v http://localhost
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Failure Patterns

`Connection refused` usually means:

- host reachable
- port closed
- service not listening
- service listening on wrong interface

`Timed out` usually means:

- firewall drop
- routing problem
- wrong IP
- server down
- cloud security group blocking

`Permission denied` over SSH usually means:

- wrong username
- wrong key
- public key missing from `authorized_keys`
- bad SSH file permissions
- password login disabled

`502 Bad Gateway` usually means:

- nginx is up
- backend is down/unreachable/wrong port

`403 Forbidden` usually means:

- service exists
- access denied by permissions/auth/nginx config

## Hands-On Labs

### Lab 1: Local Port

```bash
python3 -m http.server 8000
sudo ss -tulpn | grep ':8000'
curl http://127.0.0.1:8000
nc -vz 127.0.0.1 8000
```

Learn: port, process, HTTP, TCP test.

### Lab 2: Firewall

Use a lab VM, not an important remote server:

```bash
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw allow 8000/tcp
sudo ufw status numbered
sudo ufw delete allow 8000/tcp
```

Learn: allow, delete, default deny.

### Lab 3: Docker DNS

```bash
docker network create lab-net
docker run -d --name web --network lab-net nginx:stable
docker run -it --rm --network lab-net curlimages/curl sh
```

Inside the curl container:

```bash
curl http://web
```

Learn: container names resolve on the same Docker network.

## The 10 Commands To Burn Into Your Brain

```bash
ip addr
ip route
dig +short example.com
ping 8.8.8.8
nc -vz host port
sudo ss -tulpn
sudo ufw status verbose
curl -v http://host:port
journalctl -u service -f
docker compose ps
```

## Final Mantra

Name resolves.
Route exists.
Port listens.
Firewall allows.
Process is healthy.
Logs confirm.
Identity has permission.
Data dependency works.
Recent change is understood.

If you can walk that chain calmly, you can debug almost anything.
