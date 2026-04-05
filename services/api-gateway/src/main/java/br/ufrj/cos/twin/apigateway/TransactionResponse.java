package br.ufrj.cos.twin.apigateway;

import java.math.BigDecimal;
import java.time.Instant;

public record TransactionResponse(
        Long transactionId,
        String status,
        String sourceKey,
        String destinationKey,
        String destinationName,
        BigDecimal amount,
        Long processingTimeMs,
        Instant createdAt
) {}
