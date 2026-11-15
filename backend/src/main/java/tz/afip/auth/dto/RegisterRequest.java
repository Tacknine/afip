package tz.afip.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class RegisterRequest {
    @Email @NotBlank private String email;
    @NotBlank @Size(min = 8) private String password;
    @NotBlank private String fullName;
    @NotBlank private String role;
    public String getEmail() { return email; }
    public void setEmail(String v) { this.email = v; }
    public String getPassword() { return password; }
    public void setPassword(String v) { this.password = v; }
    public String getFullName() { return fullName; }
    public void setFullName(String v) { this.fullName = v; }
    public String getRole() { return role; }
    public void setRole(String v) { this.role = v; }
}
