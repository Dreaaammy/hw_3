# P2P чат через NAT

## Запуск системы

### 1. Сервер-посредник (запускается первым)
```
python3 rendezvous_udp.py --host 0.0.0.0 --port 8888
```

### 2. Клиенты (запускаются на разных машинах)
```
# Клиент Петя
python3 p2p_udp_client.py petya 10.0.0.5 8888 --port 50000

# Клиент Вася
python3 p2p_udp_client.py vasya 10.0.0.5 8888 --port 50001
```

### 3. Мониторинг трафика (на NAT-роутере)
```
sudo tcpdump -i eth0 -nn -s 0 -A 'udp' | grep --line-buffered 'ping-from-'
```

### 4. Установка соединения (в клиенте Пети)
```
> connect vasya
```
