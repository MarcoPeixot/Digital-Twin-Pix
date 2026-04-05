package br.ufrj.cos.twin.processingcore;

import java.math.BigDecimal;

public record ProcessRequest(
        String sourceKey,
        String destinationKey,
        String destinationName,
        BigDecimal amount
) {}
