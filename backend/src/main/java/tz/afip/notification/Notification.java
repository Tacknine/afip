package tz.afip.notification;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "notifications")
public class Notification {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(nullable = false, length = 20)
    private String channel;

    @Column(nullable = false, length = 5)
    private String lang = "sw";

    @Column(nullable = false, length = 200)
    private String title;

    @Column(nullable = false, columnDefinition = "text")
    private String body;

    @Column(name = "read_at")
    private Instant readAt;

    @Column(name = "sent_at")
    private Instant sentAt;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    public Long getId() { return id; }
    public Long getUserId() { return userId; }
    public void setUserId(Long v) { this.userId = v; }
    public String getChannel() { return channel; }
    public void setChannel(String v) { this.channel = v; }
    public String getLang() { return lang; }
    public void setLang(String v) { this.lang = v; }
    public String getTitle() { return title; }
    public void setTitle(String v) { this.title = v; }
    public String getBody() { return body; }
    public void setBody(String v) { this.body = v; }
    public Instant getReadAt() { return readAt; }
    public void setReadAt(Instant v) { this.readAt = v; }
    public Instant getSentAt() { return sentAt; }
    public void setSentAt(Instant v) { this.sentAt = v; }
    public Instant getCreatedAt() { return createdAt; }
}
