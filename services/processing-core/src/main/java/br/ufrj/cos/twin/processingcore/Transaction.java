package br.ufrj.cos.twin.processingcore;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "transactions")
public class Transaction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String sourceKey;

    @Column(nullable = false)
    private String destinationKey;

    @Column(nullable = false)
    private String destinationName;

    @Column(nullable = false)
    private BigDecimal amount;

    @Column(nullable = false)
    private String status;

    @Column(nullable = false)
    private Instant createdAt;

    private Instant completedAt;

    private Long processingTimeMs;

    protected Transaction() {}

    public Transaction(String sourceKey, String destinationKey, String destinationName, BigDecimal amount) {
        this.sourceKey = sourceKey;
        this.destinationKey = destinationKey;
        this.destinationName = destinationName;
        this.amount = amount;
        this.status = "PROCESSING";
        this.createdAt = Instant.now();
    }

    public void markCompleted(long processingTimeMs) {
        this.status = "COMPLETED";
        this.completedAt = Instant.now();
        this.processingTimeMs = processingTimeMs;
    }

    public void markFailed(String reason) {
        this.status = "FAILED";
        this.completedAt = Instant.now();
    }

    public Long getId() { return id; }
    public String getSourceKey() { return sourceKey; }
    public String getDestinationKey() { return destinationKey; }
    public String getDestinationName() { return destinationName; }
    public BigDecimal getAmount() { return amount; }
    public String getStatus() { return status; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getCompletedAt() { return completedAt; }
    public Long getProcessingTimeMs() { return processingTimeMs; }
}
