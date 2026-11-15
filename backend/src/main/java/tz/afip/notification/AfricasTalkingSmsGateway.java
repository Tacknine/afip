package tz.afip.notification;

import com.africastalking.AfricasTalking;
import com.africastalking.SmsService;
import com.africastalking.sms.Recipient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@ConditionalOnProperty(name = "afip.sms.provider", havingValue = "africastalking")
public class AfricasTalkingSmsGateway implements SmsGateway {

    private static final Logger log = LoggerFactory.getLogger(AfricasTalkingSmsGateway.class);

    private final String senderId;
    private final boolean initialized;

    public AfricasTalkingSmsGateway(
            @Value("${afip.sms.username:}") String username,
            @Value("${afip.sms.apiKey:}") String apiKey,
            @Value("${afip.sms.senderId:AFIP}") String senderId) {
        this.senderId = senderId;
        boolean ok = false;
        try {
            if (username != null && !username.isBlank()
                && apiKey != null && !apiKey.isBlank()) {
                AfricasTalking.initialize(username, apiKey);
                ok = true;
                log.info("Africa's Talking SDK initialized (username={}, senderId={})",
                    username, senderId);
            } else {
                log.warn("Africa's Talking credentials missing — SMS disabled");
            }
        } catch (Exception e) {
            log.error("Failed to initialize Africa's Talking SDK: {}", e.getMessage());
        }
        this.initialized = ok;
    }

    @Override
    public boolean send(String phone, String message) {
        log.info("[AT-SDK] send() called: phone={}, message={}, initialized={}",
            phone, message, initialized);

        if (!initialized) {
            log.warn("[AT-SDK] Not initialized — skipping send to {}", phone);
            return false;
        }
        try {
            SmsService sms = AfricasTalking.getService(AfricasTalking.SERVICE_SMS);
            log.info("[AT-SDK] Got SmsService, sending...");

            List<Recipient> resp = sms.send(message, senderId,
                new String[]{phone}, true);

            log.info("[AT-SDK] Response size: {}", resp != null ? resp.size() : "null");

            if (resp != null && !resp.isEmpty()) {
                for (Recipient r : resp) {
                    log.info("[AT-SDK] to={} status={} messageId={} cost={}",
                        r.number, r.status, r.messageId, r.cost);
                }
                Recipient first = resp.get(0);
                boolean success = "Success".equalsIgnoreCase(first.status);
                log.info("[AT-SDK] Returning: {}", success);
                return success;
            }
            log.warn("[AT-SDK] Empty response — returning false");
            return false;
        } catch (Exception e) {
            log.error("[AT-SDK] Failed to send to {}: {}", phone, e.getMessage(), e);
            return false;
        }
    }

    @Override
    public String providerName() {
        return "africastalking-sdk";
    }
}
