let CLIENTS_LIST = [];
let VUES = {};

class SocketMsg {
	constructor(type, data) {
		this.type = type;
		this.data = data;
	}
}

class Client {
    constructor(nickname, host, port) {
        this.nickname = nickname;
        this.host = host;
        this.port = port;
        this.connected = false;
        this.playerCount = undefined;
        this.log = [];
        this.is_console_scrolled = false;
    }
}

function setupVues() {
	VUES.clientList = new Vue({
		el: '#clients',
		data: {
			clients_list: CLIENTS_LIST,
		}
	});
}

function getClientByNickname(nick) {
    for (let client of CLIENTS_LIST) {
        if (client.nickname === nick)
            return client;
    }
}

function handleMessage(msg) {
	console.log("msg received", msg);

	if (msg.type === "clients_list") {
        for (obj of msg.data) {
            let existingClient = getClientByNickname(obj.nickname);
            if (existingClient) {
                // Copy all updates
                Object.assign(existingClient, obj);
            }
            else {
                let newClient = new Client(obj.nickname, obj.host, obj.port);
                Object.assign(newClient, obj);
                CLIENTS_LIST.push(newClient);
                existingClient = newClient;
            }
        }
	}
    else if (msg.type === "tcpr_line") {
        let clientNick = msg.data.nickname;
        let timestamp = msg.data.timestamp;
        let content = msg.data.content;

        let client = getClientByNickname(clientNick);
        if (!client) {
            console.warn("Line received for unknown client", clientNick);
        }
        else {
            client.log.push(timestamp + " " + content);
            // Don't let log get too big
            if (client.log.length > 100) {
                client.log.shift();
            }
        }

        // Keep the console scrolled to the bottom as new lines come in
        let elem = document.querySelector("#client-"+obj.nickname+" .tcpr-console");
        if (elem)
            elem.scrollTop = elem.scrollHeight;
        else 
            console.warn("elem is null");
    }
}

function setupWebSocket() {
    let ws = new WebSocket("ws://localhost:8001");

    ws.onopen = function() {
        console.log("ws connected");
    };

    ws.onmessage = function(evt) {
        //console.log("message", evt.data);
		let msg;
		try {
			msg = JSON.parse(evt.data);
		}	
		catch(error) {
			console.warn("ws couldn't parse message:", evt.data);
			return;
		}

		handleMessage(new SocketMsg(msg.message, msg.data));
    }

	ws.onclose = function() { 
		console.warn("ws closed"); 
	};

	window.onbeforeunload = function(event) {
		ws.close();
	};
}

$(document).ready(function() {
	setupVues();
	setupWebSocket();
});
