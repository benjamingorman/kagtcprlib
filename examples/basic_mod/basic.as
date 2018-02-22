void onTick(CRules@ this) {
    if (getGameTime() % 30 == 0) {
        sendPingRequest();
    }
}

void sendPingRequest() {
    tcpr("<request><id>1</id><method>ping</method><params><foo>bar</foo></params></request>");
}
