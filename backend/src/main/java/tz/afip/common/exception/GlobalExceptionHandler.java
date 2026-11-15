package tz.afip.common.exception;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ErrorResponse> api(ApiException ex, HttpServletRequest r) {
        return ResponseEntity.status(ex.getStatus())
            .body(new ErrorResponse(ex.getStatus().value(), ex.getStatus().getReasonPhrase(),
                ex.getMessage(), r.getRequestURI()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> valid(MethodArgumentNotValidException ex, HttpServletRequest r) {
        String msg = ex.getBindingResult().getFieldErrors().stream()
            .findFirst().map(e -> e.getDefaultMessage()).orElse("Validation failed");
        return ResponseEntity.badRequest()
            .body(new ErrorResponse(400, "Bad Request", msg, r.getRequestURI()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> any(Exception ex, HttpServletRequest r) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(new ErrorResponse(500, "Internal Server Error", ex.getMessage(), r.getRequestURI()));
    }
}
