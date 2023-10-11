# Quirk 🤨

Quirk syncs Ethereum events right into your Discord channels. No fuss, all function.

## 🛠 Setup

  1. Create a quirk.yml file.
  2. Configure your bot using the YAML file.
  3. Add your bot token, Infura API key, and other configuration details to a .env file.

## 🤖 Running a Quirk Bot

Place quirk.yml in the project root and then execute the following Docker command:

```bash
docker run --name quirk --detach --rm -v $(pwd):/app kprasch/quirk:latest
```

## 📜 Logs

Monitor Quirk's activities using Docker logs.

```
docker logs -f quirk
```

## 🔨 Build

Build the Docker image from the project root.


```bash
docker build -t kprasch/quirk:latest .
```

That's it! 🍜
