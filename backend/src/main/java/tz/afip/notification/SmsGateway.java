package tz.afip.notification;

public interface SmsGateway {
    boolean send(String phone, String message);
    String providerName();
}
