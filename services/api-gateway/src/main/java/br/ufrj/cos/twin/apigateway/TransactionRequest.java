package br.ufrj.cos.twin.apigateway;

import java.math.BigDecimal;

public record TransactionRequest(
        String sourceKey,
        String destinationKey,
        BigDecimal amount
) {}
