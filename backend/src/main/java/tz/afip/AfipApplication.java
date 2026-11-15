package tz.afip;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class AfipApplication {
    public static void main(String[] args) {
        SpringApplication.run(AfipApplication.class, args);
    }
}
