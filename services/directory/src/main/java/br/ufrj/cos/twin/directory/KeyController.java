package br.ufrj.cos.twin.directory;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
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

    private final Timer lookupTimer;
    private final Counter lookupSuccessCounter;
    private final Counter lookupNotFoundCounter;

    private static final Map<String, KeyLookupResponse> SIMULATED_KEYS = Map.of(
            "email@example.com", new KeyLookupResponse("email@example.com", "Maria Silva", "001", "12345-6"),
            "11999990000", new KeyLookupResponse("11999990000", "Joao Santos", "260", "65432-1"),
            "12345678900", new KeyLookupResponse("12345678900", "Ana Oliveira", "033", "78901-2")
    );

    public KeyController(MeterRegistry meterRegistry) {
        this.lookupTimer = Timer.builder("twinpix_key_lookup_duration_seconds")
                .description("Key lookup latency")
                .publishPercentiles(0.5, 0.95, 0.99)
                .register(meterRegistry);
        this.lookupSuccessCounter = Counter.builder("twinpix_key_lookups_total")
                .tag("status", "success")
                .description("Total key lookups")
                .register(meterRegistry);
        this.lookupNotFoundCounter = Counter.builder("twinpix_key_lookups_total")
                .tag("status", "not_found")
                .description("Total key lookups")
                .register(meterRegistry);
    }

    @GetMapping("/keys/{key}")
    public ResponseEntity<KeyLookupResponse> lookup(@PathVariable String key) {
        log.info("Key lookup request: {}", key);

        Timer.Sample sample = Timer.start();

        KeyLookupResponse response = SIMULATED_KEYS.get(key);
        if (response == null) {
            lookupNotFoundCounter.increment();
            sample.stop(lookupTimer);
            log.warn("Key not found: {}", key);
            return ResponseEntity.notFound().build();
        }

        sample.stop(lookupTimer);
        lookupSuccessCounter.increment();
        log.info("Key resolved: {} -> {}", key, response.ownerName());
        return ResponseEntity.ok(response);
    }
}
