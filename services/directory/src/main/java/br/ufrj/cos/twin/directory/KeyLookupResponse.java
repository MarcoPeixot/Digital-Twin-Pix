package br.ufrj.cos.twin.directory;

public record KeyLookupResponse(
        String key,
        String ownerName,
        String bankCode,
        String accountNumber
) {}
