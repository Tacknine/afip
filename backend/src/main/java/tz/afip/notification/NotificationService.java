package tz.afip.notification;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;

@Service
public class NotificationService {

    private static final Logger log = LoggerFactory.getLogger(NotificationService.class);

    private final NotificationRepository repo;
    private final SmsGateway smsGateway;

    public NotificationService(NotificationRepository repo, SmsGateway smsGateway) {
        this.repo = repo;
        this.smsGateway = smsGateway;
        log.info("NotificationService initialized with SmsGateway: {}",
            smsGateway.getClass().getSimpleName());
    }

    @Transactional
    public Notification sendInApp(Long userId, String title, String body) {
        Notification n = new Notification();
        n.setUserId(userId);
        n.setChannel("IN_APP");
        n.setLang("sw");
        n.setTitle(title);
        n.setBody(body);
        n.setSentAt(Instant.now());
        return repo.save(n);
    }

    @Transactional
    public Notification sendSms(Long userId, String phone, String title, String body) {
        log.info("[NotificationService] sendSms() called: userId={}, phone={}, title={}",
            userId, phone, title);

        Notification n = new Notification();
        n.setUserId(userId);
        n.setChannel("SMS");
        n.setLang("sw");
        n.setTitle(title);
        n.setBody(body);

        log.info("[NotificationService] Calling smsGateway.send()...");
        boolean sent = smsGateway.send(phone, title + ": " + body);
        log.info("[NotificationService] smsGateway.send() returned: {}", sent);

        if (sent) {
            n.setSentAt(Instant.now());
            log.info("[NotificationService] sentAt set to now");
        } else {
            log.warn("[NotificationService] sentAt NOT set (pending)");
        }
        return repo.save(n);
    }

    public List<Notification> listByUser(Long userId) {
        return repo.findByUserIdOrderByCreatedAtDesc(userId);
    }

    @Transactional
    public Notification markRead(Long id) {
        Notification n = repo.findById(id).orElseThrow();
        n.setReadAt(Instant.now());
        return repo.save(n);
    }
}
