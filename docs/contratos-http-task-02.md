# Contratos HTTP Minimos - Task 02

Objetivo:
Registrar os contratos HTTP minimos do fluxo transacional implementado na task 02.

Escopo:
`api-gateway`, `directory` e `processing-core`.

Limitacoes:
documento curto, cobrindo apenas os endpoints usados no fluxo minimo atual.

## 1. API Gateway

Endpoint:
`POST /transactions`

Payload de entrada:
```json
{
  "sourceKey": "minha-chave",
  "destinationKey": "email@example.com",
  "amount": 150.00
}
```

Payload de saida:
```json
{
  "transactionId": 2,
  "status": "COMPLETED",
  "sourceKey": "minha-chave",
  "destinationKey": "email@example.com",
  "destinationName": "Maria Silva",
  "amount": 150.00,
  "processingTimeMs": 4,
  "createdAt": "2026-04-05T01:55:27.448557046Z"
}
```

Erros esperados:
```json
{ "error": "sourceKey is required" }
```
HTTP `400`

```json
{ "error": "destinationKey is required" }
```
HTTP `400`

```json
{ "error": "amount must be positive" }
```
HTTP `400`

```json
{ "error": "destination key not found" }
```
HTTP `400`

```json
{ "error": "directory service unavailable" }
```
HTTP `500`

```json
{ "error": "processing core unavailable" }
```
HTTP `500`

## 2. Directory Service

Endpoint:
`GET /keys/{key}`

Payload de entrada:
sem corpo; usa `key` no path.

Payload de saida:
```json
{
  "key": "email@example.com",
  "ownerName": "Maria Silva",
  "bankCode": "001",
  "accountNumber": "12345-6"
}
```

Erros esperados:
HTTP `404` sem corpo quando a chave nao existe.

## 3. Processing Core

Endpoint:
`POST /transactions/process`

Payload de entrada:
```json
{
  "sourceKey": "minha-chave",
  "destinationKey": "email@example.com",
  "destinationName": "Maria Silva",
  "amount": 150.00
}
```

Payload de saida:
```json
{
  "transactionId": 2,
  "status": "COMPLETED",
  "processingTimeMs": 4,
  "createdAt": "2026-04-05T01:55:27.448557046Z"
}
```

Erros esperados:
```json
{ "error": "sourceKey is required" }
```
HTTP `400`

```json
{ "error": "destinationKey is required" }
```
HTTP `400`

```json
{ "error": "destinationName is required" }
```
HTTP `400`

```json
{ "error": "amount must be positive" }
```
HTTP `400`
