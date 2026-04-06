package br.ufrj.cos.twin.directory;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class DirectoryExperimentSettings {

    private final long latencyMs;
    private final long latencyJitterMs;
    private final double errorRate;

    public DirectoryExperimentSettings(
            @Value("${experiment.latency-ms:0}") long latencyMs,
            @Value("${experiment.latency-jitter-ms:0}") long latencyJitterMs,
            @Value("${experiment.error-rate:0.0}") double errorRate
    ) {
        this.latencyMs = Math.max(0, latencyMs);
        this.latencyJitterMs = Math.max(0, latencyJitterMs);
        this.errorRate = Math.max(0.0, Math.min(1.0, errorRate));
    }

    public long latencyMs() {
        return latencyMs;
    }

    public long latencyJitterMs() {
        return latencyJitterMs;
    }

    public double errorRate() {
        return errorRate;
    }
}
