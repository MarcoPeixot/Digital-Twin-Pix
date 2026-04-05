package br.ufrj.cos.twin.processingcore;

import java.math.BigDecimal;
import java.time.Instant;

public record ProcessResponse(
        Long transactionId,
        String status,
        Long processingTimeMs,
        Instant createdAt
) {}
