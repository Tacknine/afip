package tz.afip.auth.security;

public record UserPrincipal(Long userId, String email, String role) { }
