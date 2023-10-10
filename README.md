# Quirk 🤨 - *Listen to Ethereum. Speak Discord.*

Quirk is the bot that bridges the Ethereum universe with Discord. If Ethereum sneezes, you get a tissue on Discord. It's that simple. No fluff, no jargon, just quirk.

## 🛠 Quirk Configuration 101

**Quirk up your YAML file** like this example below. Save it as \`quirk.yml\`.

```yaml
name: "Relay Name"
bot:
  token: "{{ YOUR_DISCORD_BOT_TOKEN }}"
  prefix: '!'
  subscribers:
    - name: "SubscriberName"
      channel_id: "{{ DISCORD_CHANNEL_ID }}"
      description: "Channel to Wake Up When Ethereum Sings"

web3_endpoints:
  infura: "{{ YOUR_INFURA_API_KEY }}"

publishers:
  - address: "0xYourEthereumAddressHere"
    name: "CoolEvent"
    description: "Explains Itself, Really"
    chain_id: 137
    abi_file: './abis/yourABI.json'
    events:
      - EventName1
      - EventName2
```

_Quirk is opinionated but highly customizable._

---

## 🏃‍♀️ Running Quirk: Just Do It

Make sure your directory looks like this:

```
project_root
    ├── abis
    │    └── yourABI.json
    └── quirk.yml
```

**Step 2**: To get Quirk on its feet, run:

```bash
docker run --name quirk --detach --rm -v $(pwd):/app kprasch/quirk:latest
```
_Quirk is now eavesdropping on Ethereum for you._

---

## 📜 Debugging or Stalking Quirk

To see what Quirk is up to:

```bash
docker logs -f quirk
```
_Quirk doesn't mind, it has nothing to hide._

---

## 🔨 Dockerize the Quirkiness

**Step 1**: Open your trusty terminal and move to the project's root. Then build the Docker image like this:

```bash
docker build -t kprasch/quirk:latest .
```
_Because Quirk is cool, but a Dockerized Quirk is cooler._

---

There you have it! An event bot that's as simple to set up as making instant noodles 🍜.
