package tz.afip.user.controller;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import tz.afip.user.entity.Role;
import tz.afip.user.entity.User;
import tz.afip.user.entity.UserRole;
import tz.afip.user.repository.RoleRepository;
import tz.afip.user.repository.UserRepository;
import tz.afip.user.repository.UserRoleRepository;

import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/users")
@PreAuthorize("hasRole('SUPER_ADMIN')")
public class UserAdminController {

    public record UserDto(Long id, String email, String fullName, String role, boolean enabled) {}

    private static final Set<String> ALLOWED = Set.of(
            "SUPER_ADMIN", "AGRICULTURAL_OFFICER", "FARMER", "RESEARCHER", "DATA_ANALYST");

    private final UserRepository users;
    private final RoleRepository roles;
    private final UserRoleRepository userRoles;

    public UserAdminController(UserRepository users, RoleRepository roles, UserRoleRepository userRoles) {
        this.users = users;
        this.roles = roles;
        this.userRoles = userRoles;
    }

    private static String clean(String name) {
        return name == null ? null : name.replaceFirst("^ROLE_", "");
    }

    @GetMapping
    @Transactional(readOnly = true)
    public List<UserDto> list() {
        Map<Long, String> roleNames = roles.findAll().stream()
                .collect(Collectors.toMap(Role::getId, r -> clean(r.getName())));
        Map<Long, String> roleOfUser = new HashMap<>();
        for (UserRole ur : userRoles.findAll()) {
            roleOfUser.putIfAbsent(ur.getUserId(), roleNames.get(ur.getRoleId()));
        }
        return users.findAll().stream()
                .map(u -> new UserDto(u.getId(), u.getEmail(), u.getFullName(),
                        roleOfUser.get(u.getId()), u.isEnabled()))
                .toList();
    }

    @PutMapping("/{id}/role")
    @Transactional
    public UserDto changeRole(@PathVariable Long id, @RequestBody Map<String, String> body, Authentication auth) {
        User u = users.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        if (u.getEmail().equalsIgnoreCase(auth.getName())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Huwezi kubadilisha role yako mwenyewe");
        }
        String wanted = body.get("role");
        if (wanted == null || !ALLOWED.contains(wanted)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Role si sahihi");
        }
        Role role = roles.findByName(wanted)
                .or(() -> roles.findByName("ROLE_" + wanted))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST,
                        "Role " + wanted + " haipo kwenye jedwali la roles"));
        userRoles.deleteByUserId(id);
        userRoles.flush();
        userRoles.save(new UserRole(id, role.getId()));
        return new UserDto(u.getId(), u.getEmail(), u.getFullName(), clean(role.getName()), u.isEnabled());
    }

    @DeleteMapping("/{id}")
    @Transactional
    public ResponseEntity<Void> delete(@PathVariable Long id, Authentication auth) {
        User u = users.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        if (u.getEmail().equalsIgnoreCase(auth.getName())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Huwezi kujifuta mwenyewe");
        }
        try {
            userRoles.deleteByUserId(id);
            users.delete(u);
            users.flush();
        } catch (DataIntegrityViolationException e) {
            throw new ResponseStatusException(HttpStatus.CONFLICT,
                    "Mtumiaji ana data iliyounganishwa (mashamba/arifa). Mzime badala ya kumfuta.");
        }
        return ResponseEntity.noContent().build();
    }
}