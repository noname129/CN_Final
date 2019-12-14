# Sweepers!
A competitive multiplayer version of a particular explosive-finding game.

### Usage
Run the server with
```python3 main.py -server --port=12345 ```

Start the client with ```python3 main.py```

### Structure
```
api/      client-server API definition & implementation.
client/   Client-specific logic
common/   Common logic
network/  Network primitives
server/   Server-specific logic
sprites/  Sprites, for use in client UI
util/     Misc stuff
```