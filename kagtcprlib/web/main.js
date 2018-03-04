let CLIENTS_LIST = [];
let VUES = {};
let SOCKET;

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
        this.prompt_history = [];
        this.prompt_history_index = -1;
    }
}

// Sends a message down the socket
function socketSendMsg(msg) {
    SOCKET.send(JSON.stringify({message: msg.type, data: msg.data}));
}

function sendTcprPromptLine(clientNick, line) {
    console.log("sendTcprPromptLine", clientNick, line);
    socketSendMsg(new SocketMsg("tcpr_prompt_line", {nickname: clientNick, line: line}))
}

function tcprPromptKeypress(clientNick, evt) {
    let client = getClientByNickname(clientNick);
    let prompt_input = $(evt.target);
    if (!client) {
        console.warn("tcprPromptKeypress got keypress from unknown client");
        return;
    }

    //console.log("keypress", clientNick, evt);
    if (evt.which === 13) {
        // Enter key pressed - send the line
        let line = prompt_input.val();
        prompt_input.val('');
        sendTcprPromptLine(clientNick, line);
        client.prompt_history.push(line);
        client.prompt_history_index = -1;
    }
    else if (evt.which === 38) {
        // Up arrow pressed - cycle up through history
        console.log("up pressed");
        if (client.prompt_history_index === -1) {
            client.prompt_history_index = client.prompt_history.length - 1;
        }
        else {
            client.prompt_history_index--;
        }
        console.log(client.prompt_history, client.prompt_history_index);

        if (client.prompt_history_index >= 0) {
            prompt_input.val(client.prompt_history[client.prompt_history_index]);
        }
    }
    else if (evt.which === 40) {
        // Down arrow pressed - cycle down through history
        let phi = client.prompt_history_index;
        if (0 <= phi && phi <= client.promp_history.length-1) {
            client.prompt_history_index++; 
            prompt_input.val(client.prompt_history[client.prompt_history_index]);
        }
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
    }
}

function setupWebSocket() {
    SOCKET = new WebSocket("ws://localhost:8001");

    SOCKET.onopen = function() {
        console.log("ws connected");
    };

    SOCKET.onmessage = function(evt) {
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

	SOCKET.onclose = function() { 
		console.warn("ws closed"); 
	};

	window.onbeforeunload = function(event) {
		SOCKET.close();
	};
}

$(document).ready(function() {
	setupVues();
	setupWebSocket();
});
