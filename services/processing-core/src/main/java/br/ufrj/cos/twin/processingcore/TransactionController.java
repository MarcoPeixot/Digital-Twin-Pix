package br.ufrj.cos.twin.processingcore;

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

    public TransactionController(TransactionRepository repository) {
        this.repository = repository;
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

        long start = System.currentTimeMillis();

        Transaction tx = new Transaction(
                request.sourceKey(),
                request.destinationKey(),
                request.destinationName(),
                request.amount()
        );

        tx = repository.save(tx);

        long elapsed = System.currentTimeMillis() - start;
        tx.markCompleted(elapsed);
        tx = repository.save(tx);

        log.info("Transaction {} completed in {}ms", tx.getId(), elapsed);

        return ResponseEntity.ok(new ProcessResponse(
                tx.getId(),
                tx.getStatus(),
                tx.getProcessingTimeMs(),
                tx.getCreatedAt()
        ));
    }
}
