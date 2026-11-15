package tz.afip.notification;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(name = "afip.sms.provider", havingValue = "stub", matchIfMissing = true)
public class StubSmsGateway implements SmsGateway {

    private static final Logger log = LoggerFactory.getLogger(StubSmsGateway.class);

    @Override
    public boolean send(String phone, String message) {
        log.info("[SMS-STUB] to={} message={}", phone, message);
        return true;
    }

    @Override
    public String providerName() {
        return "stub";
    }
}
