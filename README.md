# Pique 🤨

Pique syncs Ethereum events right into your Discord channels. No fuss, all function.

## 🛠 Setup

  1. Create a pique.yml file.
  2. Configure your bot using the YAML file.
  3. Add your bot token, Infura API key, and other configuration details to a .env file.

## 🤖 Running a Pique Bot

Place pique.yml in the project root and then execute the following Docker command:

```bash
docker run --name pique --detach --rm -v $(pwd):/app kprasch/pique:latest
```

## 📜 Logs

Monitor Pique's activities using Docker logs.

```
docker logs -f pique
```

## 🔨 Build

Build the Docker image from the project root.


```bash
docker build -t kprasch/pique:latest .
```

That's it! 🍜
