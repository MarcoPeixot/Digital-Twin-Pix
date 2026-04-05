package br.ufrj.cos.twin.processingcore;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class TransactionController {

    private static final Logger log = LoggerFactory.getLogger(TransactionController.class);

    private final TransactionRepository repository;
    private final Timer processingTimer;
    private final Counter processingSuccessCounter;
    private final Counter processingErrorCounter;

    public TransactionController(TransactionRepository repository, MeterRegistry meterRegistry) {
        this.repository = repository;
        this.processingTimer = Timer.builder("twinpix_processing_duration_seconds")
                .description("Transaction processing latency")
                .publishPercentiles(0.5, 0.95, 0.99)
                .register(meterRegistry);
        this.processingSuccessCounter = Counter.builder("twinpix_processing_total")
                .tag("status", "success")
                .description("Total transactions processed")
                .register(meterRegistry);
        this.processingErrorCounter = Counter.builder("twinpix_processing_total")
                .tag("status", "error")
                .description("Total transactions processed")
                .register(meterRegistry);
    }

    @PostMapping("/transactions/process")
    public ResponseEntity<?> process(@RequestBody ProcessRequest request) {
        log.info("Processing transaction: {} -> {} amount={}", request.sourceKey(), request.destinationKey(), request.amount());

        if (request.sourceKey() == null || request.sourceKey().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "sourceKey is required"));
        }
        if (request.destinationKey() == null || request.destinationKey().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "destinationKey is required"));
        }
        if (request.destinationName() == null || request.destinationName().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "destinationName is required"));
        }
        if (request.amount() == null || request.amount().signum() <= 0) {
            return ResponseEntity.badRequest().body(Map.of("error", "amount must be positive"));
        }

        Timer.Sample sample = Timer.start();

        Transaction tx = new Transaction(
                request.sourceKey(),
                request.destinationKey(),
                request.destinationName(),
                request.amount()
        );

        try {
            tx = repository.save(tx);

            long elapsed = System.currentTimeMillis() - tx.getCreatedAt().toEpochMilli();
            tx.markCompleted(elapsed);
            tx = repository.save(tx);

            sample.stop(processingTimer);
            processingSuccessCounter.increment();

            log.info("Transaction {} completed in {}ms", tx.getId(), elapsed);

            return ResponseEntity.ok(new ProcessResponse(
                    tx.getId(),
                    tx.getStatus(),
                    tx.getProcessingTimeMs(),
                    tx.getCreatedAt()
            ));
        } catch (Exception e) {
            sample.stop(processingTimer);
            processingErrorCounter.increment();
            log.error("Transaction processing failed", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "processing failed"));
        }
    }
}
