package br.ufrj.cos.twin.directory;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class KeyController {

    private static final Logger log = LoggerFactory.getLogger(KeyController.class);

    private static final Map<String, KeyLookupResponse> SIMULATED_KEYS = Map.of(
            "email@example.com", new KeyLookupResponse("email@example.com", "Maria Silva", "001", "12345-6"),
            "11999990000", new KeyLookupResponse("11999990000", "Joao Santos", "260", "65432-1"),
            "12345678900", new KeyLookupResponse("12345678900", "Ana Oliveira", "033", "78901-2")
    );

    @GetMapping("/keys/{key}")
    public ResponseEntity<KeyLookupResponse> lookup(@PathVariable String key) {
        log.info("Key lookup request: {}", key);

        KeyLookupResponse response = SIMULATED_KEYS.get(key);
        if (response == null) {
            log.warn("Key not found: {}", key);
            return ResponseEntity.notFound().build();
        }

        log.info("Key resolved: {} -> {}", key, response.ownerName());
        return ResponseEntity.ok(response);
    }
}
