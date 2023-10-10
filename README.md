# Quirk

Quirk is a bot that listens to Ethereum events and publishes them to Discord.

##### Docker Build

From the project root directory, run the following command to build the docker image:

```bash
docker build -t kprasch/quirk:latest .
```

###### Configuration

Here is an example configuration file to use with the docker image:

```yaml
name: "Relay Name"
bot:
  token: "{{ DISCORD_BOT_TOKEN }}"
  prefix: '!'
  subscribers:
      - name: "Subscriber Name"
        channel_id: "{{ SUBSCRIBER_CHANNEL_ID }}"
        description: "Subscriber Description"

web3_endpoints:
  infura: "{{ INFURA_API_KEY }}"

publishers:
  - address: "0xF429C1f2d42765FE2b04CC62ab037564C2C66e5E"
    name: "Coordinator"
    description: "Lynx Domain Coordinator Events"
    chain_id: 137
    abi_file: './abis/coordinator.json'
    events:
      - StartRitual
      - EndRitual
```

##### Docker Run

```
project_root
    ├── abis
    │    └── contract.json
    └── quirk.yml

```

From the project directory, run the following command to run the docker image:

```bash
docker run -name quirk --detach --rm -v .:/app -kprasch/quirk:latest quirk
```

To read the logs from the docker image:

```bash
docker logs -f quirk
```
