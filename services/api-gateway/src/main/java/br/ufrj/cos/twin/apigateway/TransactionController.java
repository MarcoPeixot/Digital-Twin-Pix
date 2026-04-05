package br.ufrj.cos.twin.apigateway;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import java.util.Map;

@RestController
public class TransactionController {

    private static final Logger log = LoggerFactory.getLogger(TransactionController.class);

    private final RestClient restClient;
    private final String directoryUrl;
    private final String processingCoreUrl;

    public TransactionController(
            RestClient.Builder restClientBuilder,
            @Value("${services.directory.url}") String directoryUrl,
            @Value("${services.processing-core.url}") String processingCoreUrl
    ) {
        this.restClient = restClientBuilder.build();
        this.directoryUrl = directoryUrl;
        this.processingCoreUrl = processingCoreUrl;
    }

    @PostMapping("/transactions")
    public ResponseEntity<?> createTransaction(@RequestBody TransactionRequest request) {
        log.info("Received transaction request: {} -> {} amount={}", request.sourceKey(), request.destinationKey(), request.amount());

        // Validação mínima
        if (request.sourceKey() == null || request.sourceKey().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "sourceKey is required"));
        }
        if (request.destinationKey() == null || request.destinationKey().isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "destinationKey is required"));
        }
        if (request.amount() == null || request.amount().signum() <= 0) {
            return ResponseEntity.badRequest().body(Map.of("error", "amount must be positive"));
        }

        // 1. Resolver chave no Directory
        KeyLookupResult keyResult;
        try {
            keyResult = restClient.get()
                    .uri(directoryUrl + "/keys/{key}", request.destinationKey())
                    .retrieve()
                    .body(KeyLookupResult.class);
        } catch (RestClientResponseException e) {
            if (e.getStatusCode().value() == 404) {
                log.warn("Destination key not found: {}", request.destinationKey());
                return ResponseEntity.badRequest().body(Map.of("error", "destination key not found"));
            }
            log.error("Directory service error", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "directory service unavailable"));
        } catch (Exception e) {
            log.error("Directory service unreachable", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "directory service unavailable"));
        }

        log.info("Key resolved: {} -> {}", request.destinationKey(), keyResult.ownerName());

        // 2. Processar transação no Processing Core
        ProcessingResult processingResult;
        try {
            var processRequest = Map.of(
                    "sourceKey", request.sourceKey(),
                    "destinationKey", request.destinationKey(),
                    "destinationName", keyResult.ownerName(),
                    "amount", request.amount()
            );

            processingResult = restClient.post()
                    .uri(processingCoreUrl + "/transactions/process")
                    .body(processRequest)
                    .retrieve()
                    .body(ProcessingResult.class);
        } catch (Exception e) {
            log.error("Processing core error", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "processing core unavailable"));
        }

        log.info("Transaction {} completed with status {}", processingResult.transactionId(), processingResult.status());

        // 3. Montar resposta final
        var response = new TransactionResponse(
                processingResult.transactionId(),
                processingResult.status(),
                request.sourceKey(),
                request.destinationKey(),
                keyResult.ownerName(),
                request.amount(),
                processingResult.processingTimeMs(),
                processingResult.createdAt()
        );

        return ResponseEntity.ok(response);
    }

    record KeyLookupResult(String key, String ownerName, String bankCode, String accountNumber) {}
    record ProcessingResult(Long transactionId, String status, Long processingTimeMs, java.time.Instant createdAt) {}
}
