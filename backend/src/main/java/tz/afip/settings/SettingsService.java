package tz.afip.settings;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;
import java.util.regex.Pattern;

@Service
public class SettingsService {
    private static final Pattern VALID_KEY = Pattern.compile("^[a-zA-Z0-9_.]{1,100}$");
    private final AppSettingRepository repo;

    public SettingsService(AppSettingRepository repo) { this.repo = repo; }

    private static boolean isSecret(String key) {
        String k = key.toLowerCase();
        return k.endsWith("password") || k.endsWith("apikey");
    }

    /** Returns nested map. Secrets are never sent back to the browser. */
    @SuppressWarnings("unchecked")
    @Transactional(readOnly = true)
    public Map<String, Object> getAll() {
        Map<String, Object> root = new LinkedHashMap<>();
        for (AppSetting s : repo.findAll()) {
            if (isSecret(s.getKey())) continue;
            String[] parts = s.getKey().split("\\.");
            Map<String, Object> node = root;
            for (int i = 0; i < parts.length - 1; i++) {
                node = (Map<String, Object>) node.computeIfAbsent(parts[i], k -> new LinkedHashMap<String, Object>());
            }
            String v = s.getValue();
            node.put(parts[parts.length - 1],
                    "true".equals(v) ? Boolean.TRUE : "false".equals(v) ? Boolean.FALSE : v);
        }
        return root;
    }

    @Transactional
    public void saveAll(Map<String, Object> body) {
        Map<String, String> flat = new LinkedHashMap<>();
        flatten("", body, flat);
        flat.forEach((k, v) -> {
            if (!VALID_KEY.matcher(k).matches()) {
                throw new IllegalArgumentException("Invalid setting key: " + k);
            }
            if (isSecret(k) && v.isBlank()) return; // blank secret = keep current
            repo.save(new AppSetting(k, v));
        });
    }

    private void flatten(String prefix, Map<?, ?> m, Map<String, String> out) {
        m.forEach((k, v) -> {
            String key = prefix.isEmpty() ? String.valueOf(k) : prefix + "." + k;
            if (v instanceof Map<?, ?> child) flatten(key, child, out);
            else if (v != null) out.put(key, String.valueOf(v));
        });
    }
}