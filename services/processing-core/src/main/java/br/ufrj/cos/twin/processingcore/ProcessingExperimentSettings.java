package br.ufrj.cos.twin.processingcore;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class ProcessingExperimentSettings {

    private final long processingDelayMs;
    private final long processingDelayJitterMs;
    private final double errorRate;
    private final int workerCount;
    private final int queueCapacity;
    private final long queueWaitTimeoutMs;

    public ProcessingExperimentSettings(
            @Value("${experiment.processing-delay-ms:0}") long processingDelayMs,
            @Value("${experiment.processing-delay-jitter-ms:0}") long processingDelayJitterMs,
            @Value("${experiment.error-rate:0.0}") double errorRate,
            @Value("${experiment.worker-count:4}") int workerCount,
            @Value("${experiment.queue-capacity:20}") int queueCapacity,
            @Value("${experiment.queue-wait-timeout-ms:2000}") long queueWaitTimeoutMs
    ) {
        this.processingDelayMs = Math.max(0, processingDelayMs);
        this.processingDelayJitterMs = Math.max(0, processingDelayJitterMs);
        this.errorRate = Math.max(0.0, Math.min(1.0, errorRate));
        this.workerCount = Math.max(1, workerCount);
        this.queueCapacity = Math.max(0, queueCapacity);
        this.queueWaitTimeoutMs = Math.max(1, queueWaitTimeoutMs);
    }

    public long processingDelayMs() {
        return processingDelayMs;
    }

    public long processingDelayJitterMs() {
        return processingDelayJitterMs;
    }

    public double errorRate() {
        return errorRate;
    }

    public int workerCount() {
        return workerCount;
    }

    public int queueCapacity() {
        return queueCapacity;
    }

    public long queueWaitTimeoutMs() {
        return queueWaitTimeoutMs;
    }
}
